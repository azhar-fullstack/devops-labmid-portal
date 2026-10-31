"""Assignment Submission Portal — Flask app."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "devops-labmid-csc418"

DATA_FILE = Path(__file__).resolve().parent / "submissions.json"

# Simple pattern: must look like http(s)://host/...
URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def load_submissions() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_submissions(items: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def validate_submission(name: str, reg_no: str, title: str, url: str) -> list[str]:
    """Return a list of validation error messages (empty if valid)."""
    errors: list[str] = []
    if not name or not name.strip():
        errors.append("Name is required.")
    if not reg_no or not reg_no.strip():
        errors.append("Registration number is required.")
    if not title or not title.strip():
        errors.append("Assignment title is required.")
    if not url or not url.strip():
        errors.append("Submission URL is required.")
    else:
        cleaned = url.strip()
        if not URL_RE.match(cleaned):
            errors.append("Submission URL is invalid. Use a full http:// or https:// link.")
        else:
            parsed = urlparse(cleaned)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append("Submission URL is invalid. Use a full http:// or https:// link.")
    return errors


def add_submission(name: str, reg_no: str, title: str, url: str) -> tuple[bool, list[str], dict | None]:
    """Validate and save. Returns (ok, errors, saved_item_or_None)."""
    errors = validate_submission(name, reg_no, title, url)
    if errors:
        return False, errors, None
    item = {
        "name": name.strip(),
        "reg_no": reg_no.strip(),
        "title": title.strip(),
        "url": url.strip(),
    }
    items = load_submissions()
    items.append(item)
    save_submissions(items)
    return True, [], item


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "")
        reg_no = request.form.get("reg_no", "")
        title = request.form.get("title", "")
        url = request.form.get("url", "")
        ok, errors, _ = add_submission(name, reg_no, title, url)
        if ok:
            flash("Submission saved successfully.", "success")
            return redirect(url_for("index"))
        for err in errors:
            flash(err, "error")
        return render_template(
            "index.html",
            submissions=load_submissions(),
            form={"name": name, "reg_no": reg_no, "title": title, "url": url},
        )

    return render_template(
        "index.html",
        submissions=load_submissions(),
        form={"name": "", "reg_no": "", "title": "", "url": ""},
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
