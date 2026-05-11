"""Populate PostgreSQL with synthetic academic data for development (Faker).

Run after migrations: ``python -m scripts.seed_academic_data``

Requires optional dependency ``faker`` (install ``pip install -e ".[dev]"``).
"""

from __future__ import annotations

import asyncio
import random
import uuid
from decimal import Decimal

from faker import Faker
from sqlalchemy import select

from app.auth.hashing import hash_password
from app.db.session import async_session_factory
from app.domain.enums import AcademicStatus, ApplicationStatus, CourseEnrollmentStatus
from app.models.course import Course
from app.models.course_enrollment import CourseEnrollment
from app.models.enrollment_application import EnrollmentApplication
from app.models.grade import Grade
from app.models.role import Role
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User


def _letter(score: Decimal) -> str | None:
    s = float(score)
    if s >= 90:
        return "A"
    if s >= 80:
        return "B"
    if s >= 70:
        return "C"
    if s >= 60:
        return "D"
    return "F"


async def main() -> None:
    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    pw_hash = hash_password("SeedPassword123!")

    async with async_session_factory() as session:
        roles_result = await session.execute(select(Role))
        roles = {r.name: r for r in roles_result.scalars().all()}
        required = {"DEAN", "TEACHER", "STUDENT"}
        missing = required.difference(roles.keys())
        if missing:
            raise RuntimeError(f"Missing roles in database (run migrations): {missing}")

        dean = User(
            email="dean.seed@university.edu",
            full_name="Seed Dean",
            password_hash=pw_hash,
            is_active=True,
        )
        dean.roles.append(roles["DEAN"])
        session.add(dean)

        teacher_rows: list[Teacher] = []
        for _ in range(10):
            u = User(
                email=fake.unique.email(),
                full_name=fake.name(),
                password_hash=pw_hash,
                is_active=True,
            )
            u.roles.append(roles["TEACHER"])
            session.add(u)
            await session.flush()
            t = Teacher(
                user_id=u.id,
                employee_id=f"EMP-{uuid.uuid4().hex[:8].upper()}",
                department=fake.job(),
            )
            session.add(t)
            teacher_rows.append(t)

        student_rows: list[Student] = []
        for _ in range(50):
            u = User(
                email=fake.unique.email(),
                full_name=fake.name(),
                password_hash=pw_hash,
                is_active=True,
            )
            u.roles.append(roles["STUDENT"])
            session.add(u)
            await session.flush()
            st = Student(
                user_id=u.id,
                student_number=f"STU-{uuid.uuid4().hex[:10].upper()}",
                enrollment_status="ENROLLED",
                academic_group=fake.random_element(elements=("CS-21", "CS-22", "IS-21")),
                specialty=fake.random_element(elements=("Computer Science", "Information Systems")),
                enrollment_date=fake.date_between(start_date="-4y", end_date="today"),
                academic_status=AcademicStatus.ACTIVE.value,
            )
            session.add(st)
            student_rows.append(st)

        await session.flush()

        courses: list[Course] = []
        for i in range(15):
            teacher_entity = teacher_rows[i % len(teacher_rows)]
            c = Course(
                code=f"CRS-{100 + i}",
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=200),
                credits=Decimal(str(fake.random_int(min=2, max=5))),
                teacher_id=teacher_entity.id,
            )
            session.add(c)
            courses.append(c)

        await session.flush()

        enroll_pairs: list[tuple[uuid.UUID, uuid.UUID]] = []
        for st in student_rows:
            picks = random.sample(courses, k=random.randint(5, 8))
            for c in picks:
                ce = CourseEnrollment(
                    student_id=st.id,
                    course_id=c.id,
                    status=CourseEnrollmentStatus.ACTIVE.value,
                )
                session.add(ce)
                enroll_pairs.append((st.id, c.id))

        await session.flush()

        grade_count = 0
        for student_id, course_id in enroll_pairs:
            score = Decimal(str(round(random.uniform(55.0, 99.0), 2)))
            g = Grade(
                student_id=student_id,
                course_id=course_id,
                score=score,
                letter_grade=_letter(score),
            )
            session.add(g)
            grade_count += 1

        assert grade_count >= 300

        for idx, st in enumerate(student_rows):
            term = f"202{idx % 9}-{idx:03d}"
            status_pick = random.choice(
                [
                    ApplicationStatus.ENROLLED.value,
                    ApplicationStatus.ENROLLED.value,
                    ApplicationStatus.REJECTED.value,
                    ApplicationStatus.PENDING.value,
                    ApplicationStatus.UNDER_REVIEW.value,
                ],
            )
            app = EnrollmentApplication(
                applicant_user_id=st.user_id,
                status=status_pick,
                program_code=f"PRG-{idx:04d}",
                intake_term=term,
                statement=fake.text(max_nb_chars=400) if random.random() > 0.3 else None,
                resulting_student_id=st.id if status_pick == ApplicationStatus.ENROLLED.value else None,
            )
            session.add(app)

        await session.commit()
        print(f"Seed complete: {len(teacher_rows)} teachers, {len(student_rows)} students, {len(courses)} courses.")
        print(f"Created {grade_count} grades and one enrollment application per student.")


if __name__ == "__main__":
    asyncio.run(main())
