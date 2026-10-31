"""
Build a Lab Mid test-report.json from pytest JSON output and POST it
to the local receiver URL (via tunnel when running on GitHub Actions).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    pytest_json = Path(sys.argv[1] if len(sys.argv) > 1 else "pytest-report.json")
    if not pytest_json.exists():
        print(f"Missing pytest report: {pytest_json}", file=sys.stderr)
        return 1

    raw = json.loads(pytest_json.read_text(encoding="utf-8"))
    tests = []
    for t in raw.get("tests", []):
        outcome = t.get("outcome", "unknown")
        failure = None
        if outcome == "failed":
            call = t.get("call") or {}
            failure = call.get("longrepr") or t.get("longrepr") or "failed"
            if not isinstance(failure, str):
                failure = str(failure)
        tests.append(
            {
                "name": t.get("nodeid", "unknown"),
                "result": outcome,
                "failure_message": failure,
            }
        )

    summary = raw.get("summary", {})
    total = int(summary.get("total", len(tests)))
    passed = int(summary.get("passed", 0))
    failed = int(summary.get("failed", 0))
    overall = "passed" if failed == 0 and total > 0 else "failed"

    report = {
        "repository": os.environ.get("GITHUB_REPOSITORY", "local/devops-labmid-portal"),
        "branch": os.environ.get("GITHUB_REF_NAME", "local"),
        "commit_sha": os.environ.get("GITHUB_SHA", "local"),
        "pipeline_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": tests,
        "total": total,
        "passed": passed,
        "failed": failed,
        "overall_status": overall,
    }

    # Always write a local copy in CI workspace too (artifact backup)
    Path("test-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Wrote workspace test-report.json")

    receiver = os.environ.get("REPORT_RECEIVER_URL", "").rstrip("/")
    if not receiver:
        print("REPORT_RECEIVER_URL not set — skipped remote delivery")
        return 0 if overall == "passed" else 1

    url = receiver if receiver.endswith("/report") else receiver + "/report"
    data = json.dumps(report).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            # Bypass ngrok free-tier browser interstitial for CI clients
            "ngrok-skip-browser-warning": "true",
            "User-Agent": "GitHubActions-LabMid-Report/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"Posted report to {url} -> HTTP {resp.status}")
    except urllib.error.URLError as exc:
        print(f"WARNING: could not reach receiver at {url}: {exc}", file=sys.stderr)
        # Still exit non-zero if tests failed; delivery failure should not hide test failure
        return 0 if overall == "passed" else 1

    return 0 if overall == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
