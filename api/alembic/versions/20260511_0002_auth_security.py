"""Authentication sessions, password history, login telemetry, and RBAC seed."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260511_0002"
down_revision = "20260510_0001"
branch_labels = None
depends_on = None

_ROLE_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "edu.student-platform.roles")


def _role_id(name: str) -> uuid.UUID:
    return uuid.uuid5(_ROLE_NAMESPACE, name)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("users", "failed_login_count", server_default=None)

    op.create_table(
        "refresh_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("refresh_jti", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=128), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["replaced_by_session_id"], ["refresh_sessions.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("refresh_jti", name="uq_refresh_sessions_refresh_jti"),
    )
    op.create_index("ix_refresh_sessions_user_expires", "refresh_sessions", ["user_id", "expires_at"])
    op.create_index("ix_refresh_sessions_family_id", "refresh_sessions", ["family_id"])
    op.create_index("ix_refresh_sessions_revoked_at", "refresh_sessions", ["revoked_at"])

    op.create_table(
        "login_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("attempted_email", sa.String(length=320), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=128), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_login_attempts_email_created",
        "login_attempts",
        ["attempted_email", "created_at"],
    )
    op.create_index(
        "ix_login_attempts_ip_created",
        "login_attempts",
        ["ip_address", "created_at"],
    )
    op.create_index(
        "ix_login_attempts_user_created",
        "login_attempts",
        ["user_id", "created_at"],
    )

    op.create_table(
        "password_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_password_history_user_created",
        "password_history",
        ["user_id", "created_at"],
    )

    role_definitions = (
        ("STUDENT", "Student role"),
        ("TEACHER", "Teacher role"),
        ("DEAN", "Dean role"),
        ("ADMIN", "Administrator role"),
    )
    for role_name, description in role_definitions:
        op.execute(
            sa.text(
                """
                INSERT INTO roles (id, name, description, created_at, updated_at)
                VALUES (:id, :name, :description, timezone('utc', now()), timezone('utc', now()))
                ON CONFLICT (name) DO NOTHING
                """,
            ).bindparams(
                id=_role_id(role_name),
                name=role_name,
                description=description,
            ),
        )


def downgrade() -> None:
    op.drop_index("ix_password_history_user_created", table_name="password_history")
    op.drop_table("password_history")

    op.drop_index("ix_login_attempts_user_created", table_name="login_attempts")
    op.drop_index("ix_login_attempts_ip_created", table_name="login_attempts")
    op.drop_index("ix_login_attempts_email_created", table_name="login_attempts")
    op.drop_table("login_attempts")

    op.drop_index("ix_refresh_sessions_revoked_at", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_family_id", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user_expires", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")

    op.drop_column("users", "last_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")
