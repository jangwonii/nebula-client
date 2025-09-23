"""Generate JSON snapshots for directory contents via recursive traversal."""

from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from app.services.folder_inspection import DirectoryInspectionError, resolve_directory


logger = logging.getLogger(__name__)

_SNAPSHOT_ENV_VAR = "SNAPSHOT_DIR"
_DEFAULT_SNAPSHOT_DIR = "snapshots"


@dataclass(frozen=True)
class SnapshotEntry:
    """Structured metadata describing a filesystem entry."""

    relative_path: str
    absolute_path: str
    is_directory: bool
    size_bytes: int
    modified_at: datetime

    @classmethod
    def from_path(cls, root: Path, path: Path) -> "SnapshotEntry":
        try:
            stats = path.stat()
        except FileNotFoundError as exc:
            raise DirectoryInspectionError("스냅샷 대상 파일을 찾을 수 없습니다.") from exc
        except PermissionError as exc:
            raise DirectoryInspectionError("파일에 접근 권한이 없습니다.") from exc

        is_directory = path.is_dir()
        return cls(
            relative_path=str(path.relative_to(root)),
            absolute_path=str(path),
            is_directory=is_directory,
            size_bytes=0 if is_directory else stats.st_size,
            modified_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "absolute_path": self.absolute_path,
            "is_directory": self.is_directory,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at.isoformat(),
        }


@dataclass(frozen=True)
class SnapshotPage:
    """Represents a single JSON snapshot file for a directory."""

    page: int
    path: Path
    entry_count: int


@dataclass(frozen=True)
class FolderSnapshotResult:
    """Outcome details for a directory snapshot request."""

    directory: str
    generated_at: datetime
    total_entries: int
    page_size: Optional[int]
    pages: List[SnapshotPage]

    @property
    def page_count(self) -> int:
        return len(self.pages)


def snapshot_directory(raw_path: str, page_size: Optional[int] = None) -> FolderSnapshotResult:
    """Traverse a directory recursively and persist metadata snapshots to disk."""

    directory = resolve_directory(raw_path)
    logger.info('디렉터리 스냅샷 시작: path=%s, page_size=%s', directory, page_size)
    entries = list(_iter_snapshot_entries(directory))
    logger.info('항목 수집 완료: path=%s, entries=%d', directory, len(entries))
    generated_at = datetime.now(timezone.utc)

    chunks = _chunk_entries(entries, page_size)
    if not chunks:
        chunks = [entries]

    snapshot_root = _ensure_snapshot_root()
    pages: List[SnapshotPage] = []

    for index, chunk in enumerate(chunks, start=1):
        output_path = _build_snapshot_path(snapshot_root, directory, generated_at, index, len(chunks))
        logger.info(
            '스냅샷 파일 생성: path=%s, page=%d/%d, entries=%d',
            output_path,
            index,
            len(chunks),
            len(chunk),
        )
        _write_snapshot_file(
            output_path=output_path,
            directory=directory,
            generated_at=generated_at,
            total_entries=len(entries),
            page_index=index,
            page_count=len(chunks),
            page_size=page_size,
            entries=chunk,
        )
        pages.append(SnapshotPage(page=index, path=output_path, entry_count=len(chunk)))

    return FolderSnapshotResult(
        directory=str(directory),
        generated_at=generated_at,
        total_entries=len(entries),
        page_size=page_size,
        pages=pages,
    )


def _ensure_snapshot_root() -> Path:
    configured = os.getenv(_SNAPSHOT_ENV_VAR, _DEFAULT_SNAPSHOT_DIR)
    root = Path(configured).expanduser().resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DirectoryInspectionError("스냅샷 디렉터리를 생성할 수 없습니다.") from exc
    return root


def _iter_snapshot_entries(root: Path) -> Iterable[SnapshotEntry]:
    for current_dir, dirnames, filenames in os.walk(root):
        current_path = Path(current_dir)

        dirnames[:] = sorted(
            [name for name in dirnames if not name.startswith(".")],
            key=lambda name: name.lower(),
        )
        visible_files = sorted(
            [name for name in filenames if not name.startswith(".")],
            key=lambda name: name.lower(),
        )

        for directory_name in dirnames:
            directory_path = current_path / directory_name
            yield SnapshotEntry.from_path(root, directory_path)

        for file_name in visible_files:
            file_path = current_path / file_name
            yield SnapshotEntry.from_path(root, file_path)


def _chunk_entries(entries: list[SnapshotEntry], page_size: Optional[int]) -> list[list[SnapshotEntry]]:
    if page_size is None or page_size <= 0:
        return [entries]

    chunks: list[list[SnapshotEntry]] = []
    for start in range(0, len(entries), page_size):
        chunks.append(entries[start : start + page_size])
    return chunks


def _build_snapshot_path(
    snapshot_root: Path,
    directory: Path,
    generated_at: datetime,
    page_index: int,
    page_count: int,
) -> Path:
    slug = directory.name or "root"
    safe_slug = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in slug)
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_p{page_index:03d}" if page_count > 1 else ""
    filename = f"{safe_slug}_{timestamp}{suffix}.json"
    return snapshot_root / filename


def _write_snapshot_file(
    output_path: Path,
    directory: Path,
    generated_at: datetime,
    total_entries: int,
    page_index: int,
    page_count: int,
    page_size: Optional[int],
    entries: list[SnapshotEntry],
) -> None:
    payload = {
        "directory": str(directory),
        "generated_at": generated_at.isoformat(),
        "page": page_index,
        "page_count": page_count,
        "page_size": page_size,
        "total_entries": total_entries,
        "entries": [entry.to_dict() for entry in entries],
    }

    try:
        with output_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise DirectoryInspectionError("스냅샷 파일을 저장할 수 없습니다.") from exc
