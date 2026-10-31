"""Send Lab Mid test-report.json by email (bonus). Credentials via env/secrets."""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path


def main() -> int:
    report_path = Path(sys.argv[1] if len(sys.argv) > 1 else "test-report.json")
    if not report_path.exists():
        print(f"Missing report: {report_path}", file=sys.stderr)
        return 1

    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USERNAME", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    mail_to = os.environ.get("REPORT_EMAIL_TO", "").strip()
    mail_from = os.environ.get("REPORT_EMAIL_FROM", user).strip()
    port = int(os.environ.get("SMTP_PORT", "587"))

    if not all([host, user, password, mail_to, mail_from]):
        print("Email secrets not fully configured — skipping email send")
        return 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    overall = report.get("overall_status", "unknown")
    sha = (report.get("commit_sha") or "")[:12]
    passed = report.get("passed", 0)
    failed = report.get("failed", 0)
    total = report.get("total", 0)
    repo = report.get("repository", "")
    run_id = report.get("pipeline_run_id", "")

    lines = [
        f"DevOps Lab Mid — CI Test Report",
        f"Repository: {repo}",
        f"Branch: {report.get('branch')}",
        f"Commit: {report.get('commit_sha')}",
        f"Pipeline run: {run_id}",
        f"Timestamp: {report.get('execution_timestamp')}",
        f"Overall: {overall}",
        f"Counts: passed={passed} failed={failed} total={total}",
        "",
        "Individual results:",
    ]
    for t in report.get("tests", []):
        lines.append(f"- {t.get('name')}: {t.get('result')}")
        if t.get("failure_message"):
            msg = str(t["failure_message"]).splitlines()[0][:240]
            lines.append(f"  failure: {msg}")

    subject = f"[Lab Mid CI] {overall.upper()} — {repo} @ {sha} ({passed}/{total} passed)"
    body = "\n".join(lines)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(body)
    msg.add_attachment(
        report_path.read_bytes(),
        maintype="application",
        subtype="json",
        filename="test-report.json",
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=45) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(user, password)
        server.send_message(msg)

    print(f"Email sent to {mail_to} subject={subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
