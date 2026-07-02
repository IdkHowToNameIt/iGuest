"""Shared helpers for safe upload reads."""


class UploadTooLargeError(ValueError):
    """Raised when an uploaded file exceeds the allowed byte size."""


def read_upload_limited(file_obj, *, max_bytes: int, label: str = "File") -> bytes:
    """Read upload bytes with a hard cap to avoid unbounded memory usage."""
    data = file_obj.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise UploadTooLargeError(f"{label} is too large (max {max_bytes} bytes).")
    return data
