from __future__ import annotations

from enum import StrEnum


class SecuritySeverity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityEventCategory(StrEnum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ACADEMIC_INTEGRITY = "academic_integrity"
    ADMINISTRATION = "administration"
    DATA_ACCESS = "data_access"
    AVAILABILITY = "availability"
