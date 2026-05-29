# USAspending Contract Alert

Monitors [USAspending.gov](https://www.usaspending.gov) and sends an **email alert** whenever the US Government awards a contract exceeding **$50 million**.

Runs automatically every hour via GitHub Actions. No server required.

---

## How It Works

1. GitHub Actions triggers the script every hour
2. `fetch_awards.py` calls the USAspending API for contracts > $50M in the last 2 hours
3. `seen_ids.py` filters out already-alerted contracts (tracked in `seen_ids.json`)
4. `alert.py` sends an HTML email with company name, amount, date, and agency
5. `seen_ids.json` is committed back to the repo so state persists across runs

---

## Setup

### 1. Fork / clone this repo

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Example | Description |
|---|---|---|
| `SMTP_HOST` | `smtp.gmail.com` | Your SMTP server |
| `SMTP_PORT` | `587` | SMTP port (587 for TLS) |
| `SMTP_USER` | `you@gmail.com` | Sender email address |
| `SMTP_PASSWORD` | `abcd efgh ijkl mnop` | Gmail App Password (not your account password) |
| `ALERT_TO` | `you@gmail.com` | Recipient(s), comma-separated |

#### Gmail App Password setup
1. Enable 2-Factor Authentication on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an app password → copy the 16-character password
4. Use that as `SMTP_PASSWORD`

### 3. Enable GitHub Actions

Make sure Actions are enabled in your repo (Settings → Actions → Allow all actions).

### 4. Test manually

Go to **Actions → Contract Alert → Run workflow** to trigger a test run immediately.

---

## File Structure

```
usaspending-alert/
├── main.py              # Orchestrator
├── fetch_awards.py      # USAspending API client
├── seen_ids.py          # Deduplication logic
├── alert.py             # Email sender
├── seen_ids.json        # Persisted alert history (auto-updated)
├── requirements.txt
└── .github/
    └── workflows/
        └── alert.yml    # GitHub Actions cron job
```

---

## API Used

- **Endpoint**: `POST https://api.usaspending.gov/api/v2/search/spending_by_award/`
- **No API key required**
- **Filter**: Contract award type codes `A, B, C, D` + `award_amounts.lower_bound = 50,000,000`
