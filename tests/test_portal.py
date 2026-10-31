"""Required Lab Mid automated tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import app as portal


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    data = tmp_path / "submissions.json"
    data.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(portal, "DATA_FILE", data)
    yield data


@pytest.fixture
def client():
    portal.app.config["TESTING"] = True
    with portal.app.test_client() as c:
        yield c


def test_complete_details_and_valid_url_are_saved(client, clean_data):
    """Complete details and a valid submission URL → saved and listed."""
    response = client.post(
        "/",
        data={
            "name": "Azhar Mehmood",
            "reg_no": "FA23-BAI-039",
            "title": "DevOps Lab Mid",
            "url": "https://github.com/azhar-fullstack/devops-labmid-portal",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Submission saved successfully." in body
    assert "Azhar Mehmood" in body
    assert "FA23-BAI-039" in body
    assert "DevOps Lab Mid" in body

    saved = json.loads(Path(clean_data).read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["reg_no"] == "FA23-BAI-039"
    assert saved[0]["url"].startswith("https://")


def test_missing_registration_number_is_rejected(client, clean_data):
    """Missing registration number → rejected with validation message."""
    response = client.post(
        "/",
        data={
            "name": "Azhar Mehmood",
            "reg_no": "",
            "title": "DevOps Lab Mid",
            "url": "https://github.com/azhar-fullstack/devops-labmid-portal",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Registration number is required." in body
    assert "Submission saved successfully." not in body

    saved = json.loads(Path(clean_data).read_text(encoding="utf-8"))
    assert saved == []


def test_invalid_submission_url_is_rejected(client, clean_data):
    """Invalid submission URL → rejected and not saved."""
    response = client.post(
        "/",
        data={
            "name": "Azhar Mehmood",
            "reg_no": "FA23-BAI-039",
            "title": "DevOps Lab Mid",
            "url": "not-a-valid-url",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Submission URL is invalid" in body
    assert "Submission saved successfully." not in body

    saved = json.loads(Path(clean_data).read_text(encoding="utf-8"))
    assert saved == []
