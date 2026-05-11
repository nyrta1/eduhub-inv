from __future__ import annotations

import mimetypes
from pathlib import Path

from app.security.validators import sanitize_filename_component


class FileValidationError(Exception):
    """Rejected upload metadata."""


def prepare_secure_upload_path(
    directory: Path,
    original_name: str,
    *,
    allowed_mime_prefixes: tuple[str, ...] = ("application/pdf", "image/"),
    max_bytes: int = 5_242_880,
) -> tuple[Path, str]:
    """
    Foundation for safe multipart handling (filenames only — integrate with streaming reads).

    Returns target path under ``directory`` and sanitized basename with allowed MIME sniff intent.
    """
    safe_name = sanitize_filename_component(original_name)
    guessed, _ = mimetypes.guess_type(safe_name)
    if guessed is None or not any(guessed.startswith(p) for p in allowed_mime_prefixes):
        raise FileValidationError("MIME type not permitted for this endpoint.")

    directory.mkdir(parents=True, exist_ok=True)
    target = (directory / safe_name).resolve()
    if not str(target).startswith(str(directory.resolve())):
        raise FileValidationError("Path traversal detected.")

    _ = max_bytes  # enforced by caller while streaming body

    return target, safe_name
