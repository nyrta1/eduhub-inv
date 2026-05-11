from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import redis.asyncio as redis
from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.hashing import hash_password, verify_password, verify_password_needs_rehash
from app.auth.jwt import (
    TokenValidationError,
    decode_access_token,
    decode_refresh_token,
    issue_access_token,
    issue_refresh_token,
)
from app.auth.permissions import RoleName, load_role_by_name
from app.auth.token_fingerprint import fingerprint_refresh_token, fingerprints_match
from app.auth.validators import normalize_email, validate_new_password
from app.core.config import Settings
from app.domain.enums import AcademicStatus
from app.models.login_attempt import LoginAttempt
from app.models.password_history import PasswordHistory
from app.models.refresh_session import RefreshSession
from app.models.student import Student
from app.models.user import User
from app.security.audit import record_security_event
from app.security.rate_limit import AuthRateLimiter


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class AuthService:
    """Coordinates credential verification, token issuance, and session lifecycle."""

    def __init__(
        self,
        session: AsyncSession,
        redis_client: redis.Redis,
        settings: Settings,
    ) -> None:
        self._session = session
        self._redis = redis_client
        self._settings = settings
        self._limiter = AuthRateLimiter(redis_client, settings)

    async def register_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> User:
        await self._limiter.enforce_register_ip(ip_address or "unknown")

        normalized_email = normalize_email(email)
        validate_new_password(password)

        existing_stmt = select(User.id).where(User.email == normalized_email)
        exists = (await self._session.execute(existing_stmt)).scalar_one_or_none()
        if exists is not None:
            await record_security_event(
                self._session,
                event_type="registration.denied.duplicate_email",
                actor_user_id=None,
                subject_user_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"reason": "duplicate_email"},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "registration_conflict", "message": "Unable to complete registration."},
            )

        password_digest = hash_password(password)
        student_role = await load_role_by_name(self._session, RoleName.STUDENT)
        if student_role is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "roles_missing", "message": "Role catalog is not initialized."},
            )

        user = User(
            email=normalized_email,
            full_name=full_name.strip(),
            password_hash=password_digest,
            is_active=True,
            failed_login_count=0,
        )
        user.roles.append(student_role)
        self._session.add(user)
        await self._session.flush()

        self._session.add(
            Student(
                user_id=user.id,
                student_number=_generate_student_number(),
                enrollment_status="ENROLLED",
                academic_group="GENERAL",
                specialty=None,
                enrollment_date=date.today(),
                academic_status=AcademicStatus.ACTIVE.value,
            )
        )

        await record_security_event(
            self._session,
            event_type="user.registered",
            actor_user_id=user.id,
            subject_user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"roles": [RoleName.STUDENT.value]},
        )

        history = PasswordHistory(user_id=user.id, password_hash=password_digest)
        self._session.add(history)
        await self._session.commit()
        await self._session.refresh(user, attribute_names=["roles"])
        return user

    async def login(
        self,
        *,
        email: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[TokenPair, uuid.UUID]:
        await self._limiter.enforce_login_ip(ip_address or "unknown")

        normalized_email = normalize_email(email)
        await self._limiter.enforce_login_email(normalized_email)

        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == normalized_email)
        )
        user = (await self._session.execute(stmt)).scalar_one_or_none()

        password_valid = False
        if user is not None and user.password_hash is not None:
            password_valid = verify_password(password, user.password_hash)

        if user is None:
            await self._record_login_attempt(
                attempted_email=normalized_email,
                user_id=None,
                success=False,
                failure_reason="unknown_user",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._respond_invalid_credentials()
        elif user.deleted_at is not None:
            await self._record_login_attempt(
                attempted_email=normalized_email,
                user_id=user.id,
                success=False,
                failure_reason="deleted_user",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._respond_invalid_credentials()
        elif not user.is_active:
            await self._record_login_attempt(
                attempted_email=normalized_email,
                user_id=user.id,
                success=False,
                failure_reason="inactive_user",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._respond_invalid_credentials()
        elif user.locked_until is not None and user.locked_until > datetime.now(timezone.utc):
            await self._record_login_attempt(
                attempted_email=normalized_email,
                user_id=user.id,
                success=False,
                failure_reason="account_locked",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await record_security_event(
                self._session,
                event_type="login.blocked.locked",
                actor_user_id=user.id,
                subject_user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=None,
            )
            await self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "account_locked", "message": "Account is temporarily locked."},
            )
        elif not password_valid:
            await self._record_login_attempt(
                attempted_email=normalized_email,
                user_id=user.id,
                success=False,
                failure_reason="invalid_password",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._handle_failed_password(user, ip_address, user_agent)
            await self._respond_invalid_credentials()

        assert user is not None

        if verify_password_needs_rehash(user.password_hash or ""):
            user.password_hash = hash_password(password)

        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)

        await self._record_login_attempt(
            attempted_email=normalized_email,
            user_id=user.id,
            success=True,
            failure_reason=None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        tokens, session_id = await self._issue_session_tokens(user, ip_address, user_agent)

        await record_security_event(
            self._session,
            event_type="login.success",
            actor_user_id=user.id,
            subject_user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"session_id": str(session_id)},
        )
        await self._session.commit()
        return tokens, session_id

    async def refresh_tokens(
        self,
        *,
        refresh_token: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[TokenPair, uuid.UUID]:
        try:
            claims = decode_refresh_token(refresh_token, self._settings)
        except TokenValidationError:
            await record_security_event(
                self._session,
                event_type="token.refresh.rejected",
                actor_user_id=None,
                subject_user_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"reason": "invalid_refresh"},
            )
            await self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_refresh", "message": "Refresh token is not valid."},
            ) from None

        await self._limiter.enforce_refresh_session(str(claims.session_id))

        stmt = (
            select(RefreshSession)
            .where(RefreshSession.id == claims.session_id)
        )
        session_row = (await self._session.execute(stmt)).scalar_one_or_none()

        if session_row is None:
            await self._reject_refresh("missing_session", ip_address, user_agent)
        elif session_row.revoked_at is not None:
            await self._handle_refresh_reuse(session_row, ip_address, user_agent)
        elif session_row.expires_at < datetime.now(timezone.utc):
            await self._reject_refresh("expired_session", ip_address, user_agent)
        else:
            pepper = self._settings.resolved_token_pepper()
            if not fingerprints_match(session_row.refresh_token_hash, refresh_token, pepper):
                await self._reject_refresh("fingerprint_mismatch", ip_address, user_agent)
            elif session_row.refresh_jti != claims.refresh_jti:
                await self._handle_refresh_reuse(session_row, ip_address, user_agent)

        stmt_user = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == claims.user_id)
        )
        user = (await self._session.execute(stmt_user)).scalar_one_or_none()
        if user is None or user.deleted_at is not None or not user.is_active:
            await self._reject_refresh("invalid_user", ip_address, user_agent)

        assert user is not None

        session_row.revoked_at = datetime.now(timezone.utc)

        new_session_id = uuid.uuid4()
        new_family_id = session_row.family_id
        new_refresh_jti = uuid.uuid4()
        access_jti = uuid.uuid4()

        refresh_jwt = issue_refresh_token(
            user_id=user.id,
            session_id=new_session_id,
            refresh_jti=new_refresh_jti,
            family_id=new_family_id,
            settings=self._settings,
        )
        refresh_hash = fingerprint_refresh_token(refresh_jwt, pepper)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._settings.jwt_refresh_ttl_seconds)

        new_row = RefreshSession(
            id=new_session_id,
            user_id=user.id,
            family_id=new_family_id,
            refresh_jti=new_refresh_jti,
            refresh_token_hash=refresh_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            replaced_by_session_id=None,
        )
        session_row.replaced_by_session_id = new_session_id
        self._session.add(new_row)

        access_token = issue_access_token(
            user_id=user.id,
            session_id=new_session_id,
            access_jti=access_jti,
            settings=self._settings,
        )

        await record_security_event(
            self._session,
            event_type="token.refresh.success",
            actor_user_id=user.id,
            subject_user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "rotated_from_session": str(session_row.id),
                "rotated_to_session": str(new_session_id),
            },
        )

        await self._session.commit()

        pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_jwt,
            expires_in=self._settings.jwt_access_ttl_seconds,
        )
        return pair, new_session_id

    async def logout(
        self,
        *,
        access_token: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        try:
            claims = decode_access_token(access_token, self._settings)
        except TokenValidationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_token", "message": "Invalid access token."},
            ) from None

        stmt = select(RefreshSession).where(RefreshSession.id == claims.session_id)
        session_row = (await self._session.execute(stmt)).scalar_one_or_none()
        if session_row and session_row.revoked_at is None:
            session_row.revoked_at = datetime.now(timezone.utc)

        await self._redis.setex(
            f"auth:revoked_session:{claims.session_id}",
            self._settings.jwt_access_ttl_seconds,
            "1",
        )

        await record_security_event(
            self._session,
            event_type="logout.session",
            actor_user_id=claims.user_id,
            subject_user_id=claims.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"session_id": str(claims.session_id)},
        )
        await self._session.commit()

    async def logout_all(self, user_id: uuid.UUID, *, ip_address: str | None, user_agent: str | None) -> None:
        stmt = (
            update(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

        await self._redis.setex(
            f"auth:revoked_all:{user_id}",
            self._settings.jwt_refresh_ttl_seconds,
            "1",
        )

        await record_security_event(
            self._session,
            event_type="logout.all_sessions",
            actor_user_id=user_id,
            subject_user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=None,
        )
        await self._session.commit()

    async def change_password(
        self,
        *,
        user: User,
        current_password: str,
        new_password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        validate_new_password(new_password)

        if user.password_hash is None or not verify_password(current_password, user.password_hash):
            await record_security_event(
                self._session,
                event_type="password.change.failed",
                actor_user_id=user.id,
                subject_user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"reason": "invalid_current_password"},
            )
            await self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "invalid_credentials", "message": "Current password is incorrect."},
            )

        history_stmt = (
            select(PasswordHistory.password_hash)
            .where(PasswordHistory.user_id == user.id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(self._settings.password_history_limit)
        )
        previous_hashes = (await self._session.execute(history_stmt)).scalars().all()
        for prior_hash in previous_hashes:
            if verify_password(new_password, prior_hash):
                await record_security_event(
                    self._session,
                    event_type="password.change.rejected.history",
                    actor_user_id=user.id,
                    subject_user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=None,
                )
                await self._session.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "password_reused", "message": "Password has been used recently."},
                )

        new_hash = hash_password(new_password)
        user.password_hash = new_hash
        self._session.add(PasswordHistory(user_id=user.id, password_hash=new_hash))

        delete_sessions = delete(RefreshSession).where(RefreshSession.user_id == user.id)
        await self._session.execute(delete_sessions)

        await record_security_event(
            self._session,
            event_type="password.change.success",
            actor_user_id=user.id,
            subject_user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=None,
        )
        await self._session.commit()

    async def admin_assign_role(
        self,
        *,
        actor: User,
        target_user_id: uuid.UUID,
        new_role: RoleName,
        ip_address: str | None,
        user_agent: str | None,
    ) -> User:
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == target_user_id)
        )
        target = (await self._session.execute(stmt)).scalar_one_or_none()
        if target is None or target.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "user_not_found", "message": "User could not be located."},
            )

        role = await load_role_by_name(self._session, new_role)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "role_not_found", "message": "Role is not defined."},
            )

        previous_roles = [role.name for role in target.roles]
        target.roles.clear()
        target.roles.append(role)

        await record_security_event(
            self._session,
            event_type="role.updated",
            actor_user_id=actor.id,
            subject_user_id=target.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "previous_roles": previous_roles,
                "new_role": new_role.value,
            },
        )
        await self._session.commit()
        await self._session.refresh(target, attribute_names=["roles"])
        return target

    async def issue_tokens_for_user(
        self,
        user: User,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[TokenPair, uuid.UUID]:
        tokens, session_id = await self._issue_session_tokens(user, ip_address, user_agent)
        await record_security_event(
            self._session,
            event_type="session.issued",
            actor_user_id=user.id,
            subject_user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"session_id": str(session_id)},
        )
        await self._session.commit()
        return tokens, session_id

    async def _issue_session_tokens(
        self,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[TokenPair, uuid.UUID]:
        session_id = uuid.uuid4()
        family_id = uuid.uuid4()
        refresh_jti = uuid.uuid4()
        access_jti = uuid.uuid4()

        refresh_token = issue_refresh_token(
            user_id=user.id,
            session_id=session_id,
            refresh_jti=refresh_jti,
            family_id=family_id,
            settings=self._settings,
        )

        pepper = self._settings.resolved_token_pepper()
        refresh_hash = fingerprint_refresh_token(refresh_token, pepper)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._settings.jwt_refresh_ttl_seconds)

        row = RefreshSession(
            id=session_id,
            user_id=user.id,
            family_id=family_id,
            refresh_jti=refresh_jti,
            refresh_token_hash=refresh_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        self._session.add(row)

        access_token = issue_access_token(
            user_id=user.id,
            session_id=session_id,
            access_jti=access_jti,
            settings=self._settings,
        )

        await self._session.flush()

        pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._settings.jwt_access_ttl_seconds,
        )
        return pair, session_id

    async def _record_login_attempt(
        self,
        *,
        attempted_email: str,
        user_id: uuid.UUID | None,
        success: bool,
        failure_reason: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        attempt = LoginAttempt(
            attempted_email=attempted_email,
            user_id=user_id,
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(attempt)

    async def _handle_failed_password(
        self,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        user.failed_login_count += 1
        if user.failed_login_count >= self._settings.auth_max_failed_logins:
            lock_until = datetime.now(timezone.utc) + timedelta(
                seconds=self._settings.auth_lockout_seconds,
            )
            user.locked_until = lock_until
            await record_security_event(
                self._session,
                event_type="account.lockout",
                actor_user_id=user.id,
                subject_user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"until": lock_until.isoformat()},
            )

    async def _respond_invalid_credentials(self) -> None:
        await self._session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Invalid email or password."},
        )

    async def _reject_refresh(
        self,
        reason: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        await record_security_event(
            self._session,
            event_type="token.refresh.rejected",
            actor_user_id=None,
            subject_user_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"reason": reason},
        )
        await self._session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_refresh", "message": "Refresh token is not valid."},
        ) from None

    async def _handle_refresh_reuse(
        self,
        session_row: RefreshSession,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        await self._revoke_family(session_row.family_id)
        await record_security_event(
            self._session,
            event_type="token.refresh.reuse_detected",
            actor_user_id=session_row.user_id,
            subject_user_id=session_row.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"family_id": str(session_row.family_id)},
        )
        await self._session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "refresh_reuse", "message": "Session has been invalidated."},
        ) from None

    async def _revoke_family(self, family_id: uuid.UUID) -> None:
        stmt = (
            select(RefreshSession).where(
                RefreshSession.family_id == family_id,
                RefreshSession.revoked_at.is_(None),
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        now = datetime.now(timezone.utc)
        for row in rows:
            row.revoked_at = now
            await self._redis.setex(
                f"auth:revoked_session:{row.id}",
                self._settings.jwt_access_ttl_seconds,
                "1",
            )


def _generate_student_number() -> str:
    return f"STU-{uuid.uuid4().hex[:10].upper()}"
