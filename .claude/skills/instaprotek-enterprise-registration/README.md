# InstaProtek Enterprise Registration — Operator Guide

This skill processes a single InstaProtek enterprise sale registration from start to finish: validates the file, resolves any SKU-style model numbers via the CRM Brand menu (with web search fallback), drives the qa.crm.instaprotek.com UI via headless Playwright, and posts the result to RingCentral.

## One-time setup

1. **Populate credentials.** Open `credentials.json` in the project root and fill in:
   ```json
   {
     "username": "your-crm-username",
     "password": "your-crm-password"
   }
   ```
   This file is gitignored and never committed.

2. **Install Python dependencies and the Chromium browser.** The first run does this automatically, but you can do it ahead of time:
   ```bash
   pip install --break-system-packages playwright pdfplumber openpyxl requests
   python -m playwright install chromium
   ```

3. **First run = headed mode.** The CRM DOM selectors are not yet captured. Run with `--headed` so you can watch and the script can record selectors into `config/selectors.json`.

## Running

Drop **exactly one** Purchase Order PDF and **exactly one** bulk registration CSV or XLSX into `input/`. From the project root:

```bash
# Standard run (default after first-run setup)
python .claude/skills/instaprotek-enterprise-registration/scripts/run.py

# First-ever run, or to debug
python .claude/skills/instaprotek-enterprise-registration/scripts/run.py --headed --verbose

# Validate only, do not touch the CRM or webhook
python .claude/skills/instaprotek-enterprise-registration/scripts/run.py --dry-run

# Force a fresh read of the CRM Brand menu
python .claude/skills/instaprotek-enterprise-registration/scripts/run.py --refresh-brand-menu
```

## Outputs

**On success**, all artifacts move to `processed/YYYY-MM-DD_HHMMSS_PO<#####>/`:

- The corrected registration file under the original filename (this is what was uploaded to the CRM)
- The untouched input file with an `.original` suffix
- The PO PDF
- `validation_report.json` — what was auto-corrected, what was cross-validated
- `run_log.txt` — full structured log of every step
- `webhook_response.json` — RingCentral response
- `screenshots/` — per-step browser screenshots

**On failure**, the input files stay in `input/` so you can fix the issue and re-run. Failure artifacts land in `processed/failures/YYYY-MM-DD_HHMMSS_PO<#####>/` and a failure payload is posted to RingCentral with the reason.

## What gets auto-corrected silently

- Trailing/leading whitespace in any string cell
- `"yes"` / `"no"` normalized to `"Yes"` / `"No"`
- Manufacturer capitalization (per SOP rule: first letter uppercase, rest lowercase) — only as a starting point; the final value is always determined by Brand menu match
- Model Number SKU codes (e.g., `SM-A156UZKDXAA`) replaced with the consumer model name (e.g., `Galaxy A15 5G`), with Manufacturer adjusted accordingly (e.g., `Samsung` → `Samsung Galaxy`) per the Brand menu

## Hard-fail conditions

The run stops, files stay in `input/`, and a failure payload is sent to RingCentral if:

- Zero or more than one PO PDF in `input/`
- Zero or more than one CSV/XLSX in `input/`
- CSV row count does not equal PO quantity
- CSV end-user name does not match PO end-user
- A row's `(Manufacturer, Model Number)` cannot be reconciled against the CRM Brand menu, even after web search
- CRM login fails
- Any required CRM UI element cannot be located
- Webhook URL is unreachable (success payload only — failure payloads retry with extended timeout)

## Configuration

| File | Purpose |
|---|---|
| `config/settings.json` | CRM URL, company, vertical, webhook URL, runtime defaults |
| `config/selectors.json` | CRM DOM selectors — empty placeholders filled during first headed run |
| `config/brand_menu_cache.json` | Brand menu snapshot from the CRM (refreshed when stale) |
| `config/sku_to_model.json` | Persistent cache of resolved SKU → model lookups |
| `.auth/storage_state.json` | Playwright session storage (gitignored) |

## Troubleshooting

- **"Workspace still starting"** — wait a few seconds and re-run.
- **Login failure** — check `credentials.json`. If MFA is enabled on the account, the script will fail. Use a non-MFA service account.
- **Selector not found** — re-run with `--headed --verbose`. The CRM may have changed its UI; update `config/selectors.json` accordingly.
- **Model reconciliation fails for a known-good SKU** — check `config/brand_menu_cache.json` to confirm the brand exists in the CRM. Run with `--refresh-brand-menu` if stale.
