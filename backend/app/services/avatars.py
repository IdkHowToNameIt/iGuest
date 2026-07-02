"""
Profile-picture storage for admin and host accounts.

Images are saved as plain files under AVATAR_DIR and served by the backend's
/uploads static mount (see app/main.py) — no image processing (resize/crop):
at the size these are ever displayed (a small circular avatar), CSS
`object-fit: cover` fully handles non-square source images, and the accounts
that use this (one admin, a handful of hosts) upload rarely enough that a
few extra kilobytes on disk isn't worth a new imaging dependency.

AVATAR_DIR is a module-level variable (not a constant baked into function
bodies) so tests can point it at a tmp_path.
"""

import uuid
from pathlib import Path

AVATAR_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "avatars"

# Content-type allowlist → file extension used for the stored filename.
ALLOWED_CONTENT_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


class AvatarError(Exception):
    """Raised when an uploaded avatar fails validation. `code` is machine-readable."""

    code = "avatar_error"


class UnsupportedTypeError(AvatarError):
    code = "unsupported_type"


class TooLargeError(AvatarError):
    code = "too_large"


def save_avatar(content: bytes, content_type: str) -> str:
    """Validate and persist an avatar image. Returns the served path.

    Raises UnsupportedTypeError / TooLargeError on invalid input.
    """
    ext = ALLOWED_CONTENT_TYPES.get(content_type)
    if ext is None:
        raise UnsupportedTypeError(
            f"Unsupported image type: {content_type}. Use PNG, JPEG or WebP."
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise TooLargeError("Image is too large (max 5 MB).")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    (AVATAR_DIR / filename).write_bytes(content)
    return f"/uploads/avatars/{filename}"


def delete_avatar_file(avatar_path: str | None) -> None:
    """Best-effort removal of a previously saved avatar file. Never raises."""
    if not avatar_path:
        return
    filename = Path(avatar_path).name
    if not filename:
        return
    try:
        avatar_dir = AVATAR_DIR.resolve(strict=False)
        candidate = (AVATAR_DIR / filename).resolve(strict=False)
        # Only allow deletions inside the avatar directory even if the stored
        # path is tampered with.
        if candidate.parent != avatar_dir:
            return
        candidate.unlink()
    except OSError:
        pass
