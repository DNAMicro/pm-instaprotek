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
- **Version control:** after each regression cycle, commit the updated tracker, checklist, and
  defect log and push to git — `git add . && git commit -m "Regression run <version>" && git push`.
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
