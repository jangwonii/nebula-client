"""Tests for the recursive folder snapshot API endpoint."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_snapshot_creates_single_file(tmp_path, monkeypatch):
    target_dir = tmp_path / "source"
    target_dir.mkdir()

    (target_dir / "alpha.txt").write_text("alpha", encoding="utf-8")
    nested_dir = target_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "beta.txt").write_text("beta", encoding="utf-8")
    hidden_dir = target_dir / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "secret.txt").write_text("secret", encoding="utf-8")

    snapshot_root = tmp_path / "snapshots"
    monkeypatch.setenv("SNAPSHOT_DIR", str(snapshot_root))

    response = client.post(
        "/folders/snapshot",
        json={"path": str(target_dir)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["directory"] == str(target_dir.resolve())
    assert payload["page_count"] == 1
    assert payload["total_entries"] == 3
    assert payload["pages"][0]["entry_count"] == 3

    snapshot_path = Path(payload["pages"][0]["path"])
    assert snapshot_path.exists()

    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    relative_paths = {entry["relative_path"] for entry in data["entries"]}
    assert "alpha.txt" in relative_paths
    assert "nested" in relative_paths
    assert "nested/beta.txt" in relative_paths
    assert not any(path.startswith(".hidden") for path in relative_paths)


def test_snapshot_honors_page_size(tmp_path, monkeypatch):
    target_dir = tmp_path / "source"
    target_dir.mkdir()

    for index in range(5):
        (target_dir / f"file_{index}.txt").write_text(f"data-{index}", encoding="utf-8")

    snapshot_root = tmp_path / "snapshots"
    monkeypatch.setenv("SNAPSHOT_DIR", str(snapshot_root))

    response = client.post(
        "/folders/snapshot",
        json={"path": str(target_dir), "page_size": 2},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["page_count"] == 3
    assert payload["page_size"] == 2
    assert [page["entry_count"] for page in payload["pages"]] == [2, 2, 1]

    for page in payload["pages"]:
        snapshot_path = Path(page["path"])
        assert snapshot_path.exists()
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
        assert len(data["entries"]) == page["entry_count"]
        assert data["page"] == page["page"]
        assert data["page_size"] == 2
