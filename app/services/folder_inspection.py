"""Services to inspect directories and retrieve file metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.schemas.folder import FileInfo, FolderContentsResponse


class DirectoryInspectionError(Exception):
    """Raised when a directory cannot be inspected."""


@dataclass(frozen=True)
class DirectoryEntry:
    """Internal representation of a directory entry."""

    name: str
    path: Path
    is_directory: bool
    size_bytes: int
    modified_at: datetime

    @classmethod
    def from_path(cls, entry_path: Path) -> "DirectoryEntry":
        stats = entry_path.stat()
        return cls(
            name=entry_path.name,
            path=entry_path,
            is_directory=entry_path.is_dir(),
            size_bytes=0 if entry_path.is_dir() else stats.st_size,
            modified_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
        )


def _normalize_directory(raw_path: str) -> Path:
    try:
        normalized = Path(raw_path).expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise DirectoryInspectionError("해당 경로가 존재하지 않습니다.") from exc

    if not normalized.is_dir():
        raise DirectoryInspectionError("디렉터리 경로를 선택해주세요.")

    return normalized


def resolve_directory(raw_path: str) -> Path:
    """Return a normalized directory path or raise a descriptive error."""

    return _normalize_directory(raw_path)


def _iter_directory_entries(directory: Path) -> Iterable[DirectoryEntry]:
    try:
        for entry in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            if entry.name.startswith("."):
                continue
            yield DirectoryEntry.from_path(entry)
    except PermissionError as exc:
        raise DirectoryInspectionError("디렉터리에 접근 권한이 없습니다.") from exc


def inspect_directory(raw_path: str) -> FolderContentsResponse:
    """Return metadata for the immediate children of the provided directory."""

    directory = resolve_directory(raw_path)
    entries = [
        FileInfo(
            name=entry.name,
            path=str(entry.path),
            is_directory=entry.is_directory,
            size_bytes=entry.size_bytes,
            modified_at=entry.modified_at,
        )
        for entry in _iter_directory_entries(directory)
    ]

    return FolderContentsResponse(directory=str(directory), entries=entries)
