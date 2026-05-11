"""Academic domain: enrollment applications, course enrollments, grade history, student profile extensions."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260512_0003"
down_revision = "20260511_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("students", sa.Column("academic_group", sa.String(length=64), nullable=True))
    op.add_column("students", sa.Column("specialty", sa.String(length=255), nullable=True))
    op.add_column("students", sa.Column("enrollment_date", sa.Date(), nullable=True))
    op.add_column("students", sa.Column("academic_status", sa.String(length=32), nullable=True))
    op.create_index("ix_students_academic_status", "students", ["academic_status"])

    op.create_table(
        "enrollment_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("applicant_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("program_code", sa.String(length=64), nullable=False),
        sa.Column("intake_term", sa.String(length=32), nullable=False),
        sa.Column("statement", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("resulting_student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["applicant_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resulting_student_id"], ["students.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_enrollment_applications_applicant_status",
        "enrollment_applications",
        ["applicant_user_id", "status"],
    )
    op.create_index("ix_enrollment_applications_status", "enrollment_applications", ["status"])

    op.create_table(
        "course_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("student_id", "course_id", name="uq_course_enrollments_student_course"),
    )
    op.create_index("ix_course_enrollments_course_id", "course_enrollments", ["course_id"])
    op.create_index("ix_course_enrollments_student_id", "course_enrollments", ["student_id"])

    op.create_table(
        "grade_histories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("new_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_grade_histories_grade_id", "grade_histories", ["grade_id"])


def downgrade() -> None:
    op.drop_index("ix_grade_histories_grade_id", table_name="grade_histories")
    op.drop_table("grade_histories")

    op.drop_index("ix_course_enrollments_student_id", table_name="course_enrollments")
    op.drop_index("ix_course_enrollments_course_id", table_name="course_enrollments")
    op.drop_table("course_enrollments")

    op.drop_index("ix_enrollment_applications_status", table_name="enrollment_applications")
    op.drop_index("ix_enrollment_applications_applicant_status", table_name="enrollment_applications")
    op.drop_table("enrollment_applications")

    op.drop_index("ix_students_academic_status", table_name="students")
    op.drop_column("students", "academic_status")
    op.drop_column("students", "enrollment_date")
    op.drop_column("students", "specialty")
    op.drop_column("students", "academic_group")
