"""
Local HTTP receiver for CI test reports.

Saves each completed report as test-report.json in the project root
(or RECEIVER_OUT_DIR). Keep this running during demos, and expose it
with a tunnel (ngrok / cloudflared) so GitHub Actions can reach it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.environ.get("RECEIVER_OUT_DIR", str(ROOT)))
OUT_FILE = OUT_DIR / "test-report.json"
HISTORY_DIR = OUT_DIR / "report-history"


@app.get("/")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "labmid-report-receiver",
            "saves_to": str(OUT_FILE),
        }
    )


@app.post("/report")
def receive_report():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "JSON body required"}), 400

    # Ensure timestamp exists
    payload.setdefault("execution_timestamp", datetime.now(timezone.utc).isoformat())

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Keep a dated copy for pass/fail demo evidence
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    status = payload.get("overall_status", "unknown")
    hist = HISTORY_DIR / f"test-report-{status}-{stamp}.json"
    hist.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[receiver] saved {OUT_FILE} overall={status}")
    return jsonify({"ok": True, "saved_as": str(OUT_FILE), "history": str(hist)}), 200


if __name__ == "__main__":
    port = int(os.environ.get("RECEIVER_PORT", "5055"))
    print(f"Report receiver on http://127.0.0.1:{port}/report")
    print(f"Writes: {OUT_FILE}")
    app.run(host="0.0.0.0", port=port, debug=False)
