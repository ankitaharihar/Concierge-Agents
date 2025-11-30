Local email testing (MailHog / SMTP debug)

Quick overview

- MailHog (recommended): lightweight web UI to capture and view emails sent by your app locally.
- Python debug SMTP: prints sent emails to the terminal (no web UI) — useful for quick checks.

1) MailHog (using Docker — easiest on Windows)

```powershell
# Run MailHog with Docker; exposes SMTP on 1025 and web UI on 8025
docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Open the MailHog UI at:
# http://localhost:8025
```

2) Python debug SMTP (no external dependency)

```powershell
# This command prints received emails to the terminal (useful when you don't need a web UI)
python -m smtpd -c DebuggingServer -n localhost:1025
```

3) Configure the app to use local SMTP

- The server prefers SendGrid when `SENDGRID_API_KEY` is present. For local testing, make sure `SENDGRID_API_KEY` is NOT set so the app falls back to SMTP.
- Example PowerShell env settings (temporary for current session):

```powershell
$env:SMTP_HOST = 'localhost'
$env:SMTP_PORT = '1025'
$env:EMAIL_FROM = 'no-reply@chronoken.test'
# Ensure SENDGRID_API_KEY is unset so SMTP fallback is used
Remove-Item Env:\SENDGRID_API_KEY -ErrorAction SilentlyContinue
```

4) Start the FastAPI server (from repo root)

```powershell
python -m uvicorn web.server:app --reload --port 8501
```

5) Trigger a welcome email

- Use the `login.html` or `signup` flows in the UI. After successful demo login/signup the frontend calls `/api/send_welcome`; the server will send the email via local SMTP.
- If using MailHog, view captured messages at `http://localhost:8025`.
- If using Python debug SMTP, check the terminal where you started it for the printed email content.

Troubleshooting

- If `/api/send_welcome` returns an error, check the uvicorn server console for exception details.
- Ensure MailHog or the debug SMTP server is running and listening on the configured port (1025 by default).
- If your SMTP server requires authentication, set `SMTP_USER`, `SMTP_PASS`, and `SMTP_TLS=true` in the environment.

Security note

- Do NOT commit production API keys (SendGrid, SMTP) to source control. Use environment variables or a secrets manager.
