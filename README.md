# DevOps Lab Mid — Assignment Submission Portal

**Course:** CSC418 · **Student:** Azhar Mehmood · **Reg:** FA23-BAI-039

Flask web portal for assignment submissions, with automated pytest coverage, GitHub Actions CI, and a local JSON report receiver (Actions → tunnel → localhost).

## Features

- Form fields: Name, Registration Number, Assignment Title, Submission URL
- Server-side validation (required fields + valid `http://` / `https://` URL)
- Saved submissions listed on the same page
- Three automated tests (happy path, missing reg no, invalid URL)
- CI posts a structured `test-report.json` to a local receiver
- Bonus: GitHub Pages status page (`docs/`) — deploys **only when tests pass**
- Bonus: Email test report after pass and fail (SMTP secrets)

## Project layout

```
portal/
  app.py                 # Flask submission portal
  templates/index.html
  static/style.css
  tests/test_portal.py   # Required automated tests
  receiver/receiver.py   # Local report endpoint → test-report.json
  scripts/build_and_send_report.py
  .github/workflows/ci.yml
  docs/index.html        # Pages status UI
```

## Quick start (local portal)

```powershell
cd portal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Run tests locally

```powershell
pytest -v
```

## Local report receiver (required for CI delivery demo)

Terminal 1 — start receiver (writes `test-report.json` in the project root):

```powershell
python receiver/receiver.py
```

Health check: http://127.0.0.1:5055/  
POST endpoint: http://127.0.0.1:5055/report

Terminal 2 — expose it so GitHub Actions can reach your PC (pick one):

```powershell
# Option A: cloudflared (free, no account needed for quick tunnel)
cloudflared tunnel --url http://127.0.0.1:5055

# Option B: ngrok
ngrok http 5055
```

Copy the public HTTPS URL (e.g. `https://xxxx.trycloudflare.com`) and add a repository secret:

| Secret name             | Value                                      |
|-------------------------|--------------------------------------------|
| `REPORT_RECEIVER_URL`   | `https://xxxx.trycloudflare.com` (or `.../report`) |

Keep the receiver + tunnel running, then push to `main` (or run **Actions → Lab Mid CI → Run workflow**).  
After the job finishes, open `test-report.json` in this folder — it should contain overall status, each test result, and failure messages when tests fail.

### Simulate a failing pipeline (demo)

Temporarily break a test assertion (or change a URL expectation), commit & push, watch CI fail, and confirm `test-report.json` shows `"overall_status": "failed"` with a failure message. Revert afterward for a green run.

## GitHub Pages (bonus)

1. Repo **Settings → Pages → Source:** GitHub Actions  
2. After a successful push to `main`, the `pages` job deploys the status site  
3. URL pattern: `https://<user>.github.io/<repo>/`

## Manual report smoke test (no Actions)

With the receiver running:

```powershell
pytest --json-report --json-report-file=pytest-report.json
$env:REPORT_RECEIVER_URL = "http://127.0.0.1:5055"
python scripts/build_and_send_report.py pytest-report.json
Get-Content .\test-report.json
```

## Demo checklist (viva)

1. Show portal in browser — valid submit appears in the list  
2. Show validation errors — empty reg no / bad URL  
3. Show `pytest -v` — 3 passing tests  
4. Show Actions green run + `test-report.json` with `"overall_status": "passed"`  
5. Show a failed run + report with failure details  
6. (Bonus) Open GitHub Pages status page  

## Author

Azhar Mehmood — FA23-BAI-039
