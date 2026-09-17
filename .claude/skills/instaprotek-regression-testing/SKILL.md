---
name: instaprotek-regression-testing
description: >-
  Run and manage regression testing for the Instaprotek portal. Use when the user wants to
  start a regression cycle, prepare a release, work with the Instaprotek test case tracker or
  defect log, fill in the pre-release checklist, or produce a release-readiness summary.
  Triggers include "Instaprotek regression", "regression run", "regression test the portal",
  "pre-release checklist", "release readiness", and "start a test cycle".
---

# Instaprotek Portal — Regression Testing

Helps plan, run, and report a regression cycle for the Instaprotek portal using a standard set
of templates. Work happens in the `PM-Instaprotek/Insta-testing` folder; create a fresh copy of
the templates for each release so every cycle keeps its own record.

## Bundled templates (`templates/`)

- `Instaprotek_Regression_Test_Plan.docx` — the standing plan: scope, approach, environments,
  roles, entry/exit criteria, defect severities, sign-off.
- `Instaprotek_Regression_Tracker.xlsx` — the test case suite (grouped by portal module), a
  Defect Log, and an auto-calculating Run Summary (pass rate, defect counts, readiness flag).
- `Instaprotek_Pre-Release_Checklist.docx` — a quick tick-box gate to run before shipping.

## Test data

- **Shared test registration — product barcode `810135810326`.** Every case that needs a
  registration or a claim uses ONE shared registration. Create it once from the mock data below
  **before** running any registration- or claim-dependent case, reuse it for all of them, and
  delete it (with its claim/order) at the end of the run. Never create a new registration per case.
  - Modules that depend on it: **Portal - Registration** and **Claim Reports**.
  - Claim filing is app-only. File the claim in the app against this same registration; that opens
    the claim record in the portal, where the claim-record cases (Claim Reports S14-34) are run.
  - Order: create the registration (portal) -> Portal Registration cases -> file the claim in the
    app -> Claim Reports record cases (S14-34) in the portal -> delete the registration and claim.

  | Field | Value |
  |---|---|
  | Product barcode | `810135810326` |
  | First / Last name | Jordan / Testwell |
  | Email | qa.jordan.testwell@example.com |
  | Phone | (202) 555-0142 |
  | Address | 100 QA Street, Testville, CA 94016 |
  | Manufacturer / Model | Samsung / SM-A156UZKDXAA |
  | Serial / IMEI | 350776860000142 |
  | Purchase date | within the last few days (inside the 30-day window and the 1-yr warranty) |
  | Price / New? | 80 / No |

- **Upload fixtures** — attach these wherever the portal or app asks for a photo or document
  (all watermarked TEST, in `Insta-testing/test-data/`): purchase receipt
  `fake_purchase_receipt.png`, damaged-device photo showing the IMEI `fake_device_photo.png`,
  repair receipt `fake_repair_receipt.png`.

## Product Plans — never create one

**Do not create, edit, or delete a Product Plan during a regression run.** Exercise the plan
cases read-only against an existing plan: open it, confirm the grid, tabs, and displayed fields,
and stop there.

Set every plan create/edit/delete case (New Plan wizard, plan Record and Details field edits,
plan teardown) to `N/A` with the note
`plan CRUD excluded — see Insta-testing/incidents/2026-09-16-production-plan-deleted.md`.

Why: on 2026-09-16 plan creation failed validation, the driver fell back to opening the first row
of an unfiltered grid, and teardown deleted a **live production plan**. 289 registrations still
reference it and 8 of its fields were never captured, so it cannot be re-keyed — only restored
from a database backup. Plan creation is the step that leads there. Skip it.

## Workflow

### 1. Start a cycle
- Ask for the release/version and target date.
- Copy `templates/Instaprotek_Regression_Tracker.xlsx` into `Insta-testing` as
  `Regression_Tracker_<version>.xlsx`, and the checklist as `Pre-Release_Checklist_<version>.docx`.
- Confirm the change list for the release and pick the in-scope cases. Always include every
  P1 (critical-path) case, then add cases for the modules that changed.

### 2. Execute
- Work down the **Test Cases** tab. For each case fill the yellow columns: Last Run Date,
  Status, Actual Result / Notes, Tester.
- Status values: `Pass`, `Fail`, `Blocked`, `Not Run`, `N/A`.

### 3. Log defects
- For every `Fail`, add a row to the **Defect Log** tab: severity (Critical/High/Medium/Low),
  priority (P1–P4), status (`Open` → `In Progress` → `Fixed - Retest` → `Closed`/`Deferred`),
  steps to reproduce, and environment.
- Put the resulting Defect ID back on the failing test case row.
- **File each genuine product bug in Jira (required).** For every `Fail` that is a real product
  defect (not a test-data/environment problem), create a Jira **Bug** and place it in the
  **"Regression Testing Bugs" sprint**, **left Unassigned**.
  Board: https://dnamicro.atlassian.net/jira/software/c/projects/INSTA/boards/2/backlog
  - Jira coordinates: cloudId `aa523965-6d7b-4eff-9dc0-e02aafcfeac9`, projectKey `INSTA`
    (project id `10001`), issueType `Bug` (id `10009`), Sprint field `customfield_10020` set to
    the **"Regression Testing Bugs"** sprint's numeric id, `assignee_account_id` omitted (unassigned).
  - Resolve the sprint id at filing time (no Agile MCP tool lists sprints): read it from
    `customfield_10020` on any issue already in that sprint via
    `sprint = "Regression Testing Bugs"`; if the sprint is still empty, ask for the sprint id.
    Never file into a different sprint as a fallback — leave it in the backlog and flag it instead.
  - Bug fields: summary `[Regression][<Module>] <short title>`; description with Steps to
    Reproduce, Expected vs. Actual, Environment (QA), the scenario ID, and severity; map severity
    → priority (Critical→Highest, High→High, Medium→Medium, Low→Low); set the `environment` field
    to the run environment; add label `regression`.
  - Put the returned Jira key (e.g. `INSTA-1234`) back on the failing scenario row and into the
    Confluence report's defect log.

### 4. Report
- The **Run Summary** tab totals everything automatically. After editing the workbook, run the
  spreadsheet recalculation step so cached values refresh before reading or sharing results.
- Produce a short release-readiness note: pass rate, open Critical/High defects, and a Go/No-go
  recommendation measured against the exit criteria in the test plan.
- **Publish the full report to Confluence (required).** Create a NEW page (never overwrite a
  prior run's page) in the **instaProtek** space (key `IE`) under the **"Regression testing"**
  folder. Coordinates: cloudId `aa523965-6d7b-4eff-9dc0-e02aafcfeac9`, spaceId `82444597`,
  parentId (folder) `822149121`. Title: `Instaprotek Regression Report — <version> (<YYYY-MM-DD>)`.
  The page must contain the FULL detail of the run:
  - Run metadata: version, environment, run date, tester/account, suite source file.
  - Run Summary: total / Pass / Fail / Blocked / Not Run / N/A counts and pass rate.
  - Per-module roll-up table (one row per module: executed, pass/fail/blocked counts).
  - **Full per-scenario results table — every single scenario tested, one row each, grouped by
    module.** Columns: Module · Scenario ID · Test Description · **Expected Result** ·
    **Actual Result** · Status (`Pass`/`Fail`/`Blocked`/`Not Run`/`N/A`) · Notes / Defect ID.
    Document expected vs. actual for EVERY scenario, not just failures — no scenario is omitted
    or collapsed. Use a Confluence status lozenge for the Status cell (green Pass / red Fail /
    yellow Blocked). For a Fail, the Actual Result must state what actually happened; for Blocked,
    the Notes must give the reason.
  - Full defect log (Defect ID, module/case, severity, priority, status, repro, environment).
  - Blocked / skipped items with the reason (e.g. role-permission cases when only one login exists).
  - Go/No-go recommendation against the exit gate.
- **Post to RingCentral (required).** After the Confluence page is published, post the
  release-readiness summary (version, pass rate, open Critical/High count, Go/No-go) to the
  RingCentral webhook, and **include the link to the Confluence page** in that post. The webhook
  URL is the one configured in `.claude/skills/instaprotek-enterprise-registration/config/settings.json`
  unless a dedicated regression channel is provided.

### 5. Clean up (teardown)
- Once results and any needed evidence are recorded, **delete all test records created during
  the run** so the environment is left clean for the next cycle. That includes the shared test
  registration (barcode `810135810326`) and any claim or order filed against it.
- Applies to the test environment (default `QA-environment`); never run destructive cleanup
  against Production.

## Conventions

- **Priorities:** P1 critical (must pass to ship) · P2 high · P3 medium · P4 low.
- **Severities:** Critical (blocks core use, no workaround) · High (major function broken,
  painful workaround) · Medium (impaired but usable) · Low (minor/cosmetic).
- **Exit gate:** all selected P1/P2 executed · no open Critical/High defects (or each accepted
  and signed off) · pass rate ≥ target (default 95%) · tracker and defect log updated · PM sign-off.

## Defaults & operating instructions

- **Default environment:** `QA-environment`. Run each regression cycle here unless told
  otherwise; use Staging for the final pre-go-live pass and Production for smoke checks only.
- **Model / token usage:** optimize token usage by matching the model to the task — a fast,
  lightweight model for mechanical steps (copying templates, filling Status cells, tallying
  counts, simple lookups), and a stronger model only for judgment-heavy steps (triaging defect
  severity, interpreting failures, writing the release-readiness recommendation).
- **Version control (required):** ALWAYS commit and push at the end of every regression cycle —
  never skip it. Run git through **bash** (git is on the bash PATH, not PowerShell); if `git` is
  not found, you are in the wrong shell — switch to bash. Commands:
  `git add -A && git commit -m "Regression run <version>" && git push`
  Remote: `https://github.com/DNAMicro/pm-instaprotek.git` (add once with `git remote add origin <url>` if unset).
- **Test data cleanup (required):** after a run, delete all test records created during it so the
  environment is left clean. Capture any needed evidence first; never run cleanup against Production.
- **Scope note:** exclude modules the team marks out of scope (currently Orders, Product Reviews,
  Device Buyback — app-only / out of scope) by setting their cases to `N/A`; do not count them in
  pass rate. Plan create/edit/delete cases are excluded the same way — see
  "Product Plans — never create one".
- **Bug filing & report delivery are REQUIRED every run** — see steps 3 (Jira) and 4 (Confluence + RingCentral).
