---
name: instaprotek-enterprise-registration
description: Process an InstaProtek enterprise sale registration end-to-end. Triggers when the user says "run instaprotek registration", "run instaprotek", "process instaprotek input", "instaprotek bulk registration", "register instaprotek sale", or any variation referencing processing the InstaProtek input folder. Also triggers when the user drops a Purchase Order PDF and a bulk registration CSV/XLSX into the project's input/ folder and asks to process them. The skill validates the registration file against the CRM brand menu, resolves SKU-style model numbers via web search, logs into qa.crm.instaprotek.com via Playwright, creates a batch, uploads the registration file, submits a transaction, posts a summary to RingCentral, and archives all artifacts.
---

# InstaProtek Enterprise Sale Registration

This skill processes a single InstaProtek enterprise sale: validates the bulk registration file against the CRM brand menu, fixes Model Number / Manufacturer rows that contain SKUs by searching online and reconciling against the CRM Brand menu, then drives the CRM UI via Playwright (Chromium) to create a batch, upload the file, and submit a transaction. A success or failure summary is posted to a RingCentral webhook.

## When to trigger this skill

Trigger this skill whenever the user asks to:

- "run instaprotek", "run instaprotek registration", "process instaprotek", "process the instaprotek input"
- "register the instaprotek sale", "submit the instaprotek batch"
- Reference processing files sitting in `input/` for the InstaProtek project
- Ask anything about the InstaProtek bulk registration workflow

If a Purchase Order PDF and a registration CSV/XLSX are present in `input/` and the user implies they want them processed, trigger this skill even if they don't use an exact phrase above.

## Prerequisites

1. `credentials.json` in the project root has been populated with the QA CRM `username` and `password`. The file is gitignored.
2. Exactly one PO PDF and exactly one CSV or XLSX file are present in `input/`. The skill hard-fails if 0 or >1 of either is present.
3. Python 3 is available. The skill auto-installs missing Python packages (`playwright`, `pdfplumber`, `openpyxl`, `requests`) and the Chromium browser binary on first run.
4. The first ever run should be performed with `--headed` so the operator can capture CRM selectors into `config/selectors.json`. Subsequent runs default to headless.

## How to run

From the project root:

```bash
python .claude/skills/instaprotek-enterprise-registration/scripts/run.py
```

Useful flags:

- `--headed` — run Playwright with a visible browser (first run, debugging)
- `--dry-run` — perform validation + brand menu resolution, but do not touch the CRM or post webhook. Files stay in `input/`.
- `--skip-webhook` — execute the run but do not post to RingCentral
- `--refresh-brand-menu` — force a re-read of the CRM Brand menu instead of using the cached copy
- `--verbose` — print full logs to stdout in addition to the run log file

## Workflow

1. Discover and validate the file pair in `input/`.
2. Parse the PO PDF: PO number, plan description, order date, quantity, end-user info.
3. Load registration file, basic cleanup (whitespace, "No" normalization).
4. Cross-validate row count vs PO quantity and end-user name vs PO end-user. Hard-fail on mismatch.
5. Launch Playwright (Chromium). Log into qa.crm.instaprotek.com. Persist storage state.
6. Read the CRM Brand menu (or use a cached copy if fresh).
7. Validate every row's `(Manufacturer, Model Number)` tuple against the Brand menu. For any miss: Google search `<Manufacturer> <Model Number> model name`, parse a candidate model name, then split-reconcile against the Brand menu to find the exact `(Manufacturer, Model Number)` entry. If reconciliation fails or is ambiguous → hard-fail.
8. Write the corrected registration file under the original filename. Preserve the input file with an `.original` suffix.
9. Drive CRM Steps 2-4: create batch, upload registration, submit transaction.
10. Post the success payload to the RingCentral webhook.
11. Move all artifacts to `processed/YYYY-MM-DD_HHMMSS_PO<#####>/`.

On any hard-fail: files stay in `input/`, failure artifacts (validation report, screenshots, log) write to `processed/failures/YYYY-MM-DD_HHMMSS_PO<#####>/`, and a failure payload is posted to RingCentral.

## Output files in each processed run folder

- `<original filename>.<ext>` — the corrected file uploaded to the CRM
- `<original filename>.original.<ext>` — the untouched input file
- `<PO filename>.pdf` — the Purchase Order
- `validation_report.json` — fixes applied and any flagged rows
- `run_log.txt` — full structured log
- `webhook_response.json` — RingCentral response
- `screenshots/` — per-CRM-step screenshots

## Configuration reference

- `config/settings.json` — CRM URL, company name, vertical, webhook URL, runtime defaults
- `config/selectors.json` — CRM DOM selectors (populated during first headed run)
- `config/brand_menu_cache.json` — cached Brand menu, refreshed when stale or with `--refresh-brand-menu`
- `config/sku_to_model.json` — persistent cache of resolved SKU lookups
