"""API tests for the folder inspection endpoint."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_inspect_folder_returns_entries(tmp_path):
    file_path = tmp_path / "document.txt"
    file_path.write_text("hello", encoding="utf-8")

    subdir = tmp_path / "nested"
    subdir.mkdir()

    hidden_file = tmp_path / ".secret"
    hidden_file.write_text("should be ignored", encoding="utf-8")

    response = client.post("/folders/inspect", json={"path": str(tmp_path)})

    assert response.status_code == 200
    payload = response.json()

    assert payload["directory"] == str(tmp_path.resolve())

    entries = {entry["name"]: entry for entry in payload["entries"]}
    assert "document.txt" in entries
    assert "nested" in entries
    assert ".secret" not in entries
    assert entries["document.txt"]["is_directory"] is False
    assert entries["nested"]["is_directory"] is True
    assert entries["document.txt"]["size_bytes"] == 5


def test_inspect_folder_with_invalid_path_returns_400(tmp_path):
    missing = tmp_path / "not_there"

    response = client.post("/folders/inspect", json={"path": str(missing)})

    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"] == "해당 경로가 존재하지 않습니다."
