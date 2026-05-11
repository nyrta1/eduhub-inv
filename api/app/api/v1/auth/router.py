from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import AuthServiceDep
from app.api.docs import ERROR_RESPONSES
from app.api.v1.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserPublic,
)
from app.auth.dependencies import CurrentUser
from app.auth.service import TokenPair
from app.auth.validators import PasswordPolicyViolation
from app.models.user import User
from app.utils.http import get_client_ip, get_user_agent

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=True)


def _token_response(pair: TokenPair) -> TokenResponse:
    expires_in = pair.expires_in or 0
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
        expires_in=expires_in,
    )


def _serialize_user(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[role.name for role in user.roles],
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a user with the STUDENT role by default. Request is security-audited and rate-limited.",
    responses={**ERROR_RESPONSES, 201: {"description": "Account created."}},
)
async def register_account(
    request: Request,
    payload: RegisterRequest,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    try:
        user = await auth_service.register_user(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
    except PasswordPolicyViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "password_policy", "message": exc.message},
        ) from exc

    return RegisterResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[role.name for role in user.roles],
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and issue access/refresh tokens",
    description="Use returned `access_token` in Swagger Authorize dialog (`Bearer <token>`). Refresh token rotation is enforced.",
    responses={**ERROR_RESPONSES, 200: {"description": "Token pair issued."}},
)
async def login(
    request: Request,
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    tokens, _session_id = await auth_service.login(
        email=str(payload.email),
        password=payload.password,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return _token_response(tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token",
    description="Consumes a valid refresh token, revokes old session token, and returns a new token pair.",
    responses={**ERROR_RESPONSES, 200: {"description": "Token pair rotated."}},
)
async def refresh_tokens(
    request: Request,
    payload: RefreshRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    tokens, _session_id = await auth_service.refresh_tokens(
        refresh_token=payload.refresh_token,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return _token_response(tokens)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout current session",
    description="Revokes the active access/refresh token family for this device session.",
    responses={**ERROR_RESPONSES, 200: {"description": "Session revoked."}},
)
async def logout_session(
    request: Request,
    auth_service: AuthServiceDep,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> MessageResponse:
    await auth_service.logout(
        access_token=credentials.credentials,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return MessageResponse()


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout from all sessions",
    description="Invalidates all active sessions for the authenticated user.",
    responses={**ERROR_RESPONSES, 200: {"description": "All sessions revoked."}},
)
async def logout_everywhere(
    request: Request,
    auth_service: AuthServiceDep,
    current_user: CurrentUser,
) -> MessageResponse:
    await auth_service.logout_all(
        current_user.id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return MessageResponse()


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get authenticated profile",
    description="Returns current user identity and assigned RBAC roles.",
    responses=ERROR_RESPONSES,
)
async def read_current_profile(current_user: CurrentUser) -> UserPublic:
    return _serialize_user(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change account password",
    description="Validates current password, enforces password policy/history, and audits security event.",
    responses={**ERROR_RESPONSES, 200: {"description": "Password changed."}},
)
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    auth_service: AuthServiceDep,
    current_user: CurrentUser,
) -> MessageResponse:
    try:
        await auth_service.change_password(
            user=current_user,
            current_password=payload.current_password,
            new_password=payload.new_password,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )
    except PasswordPolicyViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "password_policy", "message": exc.message},
        ) from exc
    return MessageResponse()
