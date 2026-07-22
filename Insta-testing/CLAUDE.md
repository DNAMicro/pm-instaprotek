# Instaprotek Regression Testing — Project Instructions

This folder holds the Instaprotek portal regression-testing kit and the per-release run records.
These instructions apply to any regression work done here.

## Defaults

- **Default test environment:** `QA-environment`. Use Staging for the final pre-go-live
  regression pass and Production for smoke checks only.

## Operating instructions

- **Optimize token usage:** match the model to the task. Use a fast, lightweight model for
  mechanical work (copying templates, filling status cells, tallying counts, simple lookups);
  use a stronger model only for judgment-heavy work (triaging defect severity, interpreting
  failures, writing the release-readiness / Go–No-go summary).
- **Bug filing (required):** file each genuine product bug found during a run as a Jira **Bug** in
  the **INSTA** project (cloudId `aa523965-6d7b-4eff-9dc0-e02aafcfeac9`), placed in the
  **"Regression Testing Bugs" sprint** — `customfield_10020` = **`5590`** (board 2) — and left
  **Unassigned**, label `regression`. **Workflow:** the project blocks empty-assignee at create
  time, so create the Bug (assignee = `5cc7aba715b0280e6fed33b9` placeholder), then immediately
  `editJiraIssue` `{"assignee": null}` and set `customfield_10020: 5590`. If sprint 5590 ever stops
  resolving, recover its id via `sprint = "Regression Testing Bugs"` on any issue already in it;
  never file into a different sprint. See the skill's "Log defects" step for fields/mapping.
- **Report delivery (required):** publish the full regression report as a NEW Confluence page in
  the **instaProtek** space (key `IE`) under the **"Regression testing"** folder — cloudId
  `aa523965-6d7b-4eff-9dc0-e02aafcfeac9`, spaceId `82444597`, parentId (folder) `822149121`.
  One page per run (never overwrite). The page must include a **full per-scenario results table —
  every scenario tested, one row each, with Expected Result vs. Actual Result and a Pass/Fail/
  Blocked status** (no scenario omitted or collapsed), plus the roll-up summary and defect log.
  Then post the release-readiness summary to RingCentral with the Confluence page **link**
  included. See the skill's Report step for the full required page contents.
- **Per-module RingCentral updates (required):** post a RingCentral update as **each module
  completes** (module name, pass/fail/blocked tally, key findings + any Jira bug keys), not only
  one summary at the end. The final full report still goes to Confluence with a link posted to
  RingCentral. Reuse the enterprise-registration webhook; payload is `{"title","text"}` markdown.
- **Version control (required):** ALWAYS commit and push at the end of every regression cycle —
  never skip it. Run git through **bash** (git is on the bash PATH here, not PowerShell):
  `git add -A && git commit -m "Regression run <version>" && git push`.
  Remote: `https://github.com/DNAMicro/pm-instaprotek.git` (add once with
  `git remote add origin <url>` if it isn't set).
- **Test data cleanup:** after running the tests, delete all test records created during the run
  so the environment is left clean. Capture any needed evidence first; never run this against Production.

## Files

- `Instaprotek_Regression_Test_Plan.docx` — standing plan (scope, approach, criteria).
- `Instaprotek_Regression_Tracker.xlsx` — test cases, defect log, auto-calculating run summary.
- `Instaprotek_Pre-Release_Checklist.docx` — pre-ship gate.
- Copy the tracker and checklist per release, e.g. `Regression_Tracker_<version>.xlsx`.

## Conventions

- **Status:** Pass / Fail / Blocked / Not Run / N/A.
- **Priority:** P1 critical (must pass) · P2 high · P3 medium · P4 low.
- **Severity:** Critical / High / Medium / Low.
- **Exit gate:** all selected P1/P2 executed · no open Critical/High defects (or accepted and
  signed off) · pass rate ≥ 95% · tracker and defect log updated · PM sign-off.
