from __future__ import annotations

from typing import Final

from pydantic import EmailStr, TypeAdapter

_EMAIL_ADAPTER = TypeAdapter(EmailStr)

_MIN_LENGTH: Final[int] = 12


class PasswordPolicyViolation(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    _EMAIL_ADAPTER.validate_python(normalized)
    return normalized


def validate_new_password(password: str) -> None:
    if len(password) < _MIN_LENGTH:
        raise PasswordPolicyViolation(
            f"Password must be at least {_MIN_LENGTH} characters long.",
        )
    categories = {
        "upper": False,
        "lower": False,
        "digit": False,
        "special": False,
    }
    for character in password:
        if character.isupper():
            categories["upper"] = True
        elif character.islower():
            categories["lower"] = True
        elif character.isdigit():
            categories["digit"] = True
        elif not character.isspace():
            categories["special"] = True

    if not all(categories.values()):
        raise PasswordPolicyViolation(
            "Password must include uppercase, lowercase, numeric, and special characters.",
        )
    if any(character.isspace() for character in password):
        raise PasswordPolicyViolation("Password must not contain whitespace.")
