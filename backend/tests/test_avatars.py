"""
Unit tests for profile-picture storage (app/services/avatars.py).

No DB, no HTTP — AVATAR_DIR is monkeypatched to a tmp_path so nothing touches
the real backend/uploads directory.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import avatars
from app.services.avatars import (
    TooLargeError,
    UnsupportedTypeError,
    delete_avatar_file,
    save_avatar,
)


@pytest.fixture(autouse=True)
def _isolated_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(avatars, "AVATAR_DIR", tmp_path)
    yield tmp_path


class TestSaveAvatar:
    def test_accepts_png(self, tmp_path):
        path = save_avatar(b"\x89PNG", "image/png")
        assert path.startswith("/uploads/avatars/")
        assert path.endswith(".png")
        assert len(list(tmp_path.iterdir())) == 1

    def test_accepts_jpeg(self, tmp_path):
        path = save_avatar(b"\xff\xd8", "image/jpeg")
        assert path.endswith(".jpg")

    def test_accepts_webp(self, tmp_path):
        path = save_avatar(b"RIFF", "image/webp")
        assert path.endswith(".webp")

    def test_rejects_unsupported_type(self):
        with pytest.raises(UnsupportedTypeError):
            save_avatar(b"GIF89a", "image/gif")

    def test_rejects_oversized_file(self, monkeypatch):
        monkeypatch.setattr(avatars, "MAX_UPLOAD_BYTES", 4)
        with pytest.raises(TooLargeError):
            save_avatar(b"way too big", "image/png")

    def test_filenames_are_unique(self, tmp_path):
        save_avatar(b"a", "image/png")
        save_avatar(b"b", "image/png")
        assert len(list(tmp_path.iterdir())) == 2


class TestDeleteAvatarFile:
    def test_deletes_existing_file(self, tmp_path):
        path = save_avatar(b"a", "image/png")
        assert len(list(tmp_path.iterdir())) == 1
        delete_avatar_file(path)
        assert len(list(tmp_path.iterdir())) == 0

    def test_missing_path_does_not_raise(self):
        delete_avatar_file("/uploads/avatars/does-not-exist.png")

    def test_none_does_not_raise(self):
        delete_avatar_file(None)

    def test_ignores_path_traversal(self, tmp_path):
        outside = tmp_path.parent / "outside.txt"
        outside.write_bytes(b"x")
        delete_avatar_file("/uploads/avatars/..\\..\\outside.txt")
        assert outside.exists()
