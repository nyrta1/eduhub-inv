from __future__ import annotations

from enum import StrEnum


class ApplicationStatus(StrEnum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ENROLLED = "ENROLLED"


class CourseEnrollmentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DROPPED = "DROPPED"


class AcademicStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PROBATION = "PROBATION"
    LEAVE = "LEAVE"
    GRADUATED = "GRADUATED"
    SUSPENDED = "SUSPENDED"


class AcademicAuditAction(StrEnum):
    APPLICATION_SUBMITTED = "academic.application.submitted"
    APPLICATION_STATUS_CHANGED = "academic.application.status_changed"
    STUDENT_UPDATED = "academic.student.updated"
    STUDENT_ENROLLED = "academic.student.enrolled"
    COURSE_CREATED = "academic.course.created"
    COURSE_UPDATED = "academic.course.updated"
    COURSE_ENROLLMENT_CREATED = "academic.course_enrollment.created"
    GRADE_CREATED = "academic.grade.created"
    GRADE_UPDATED = "academic.grade.updated"
    TEACHER_ASSIGNMENT = "academic.course.teacher_assigned"
