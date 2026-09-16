# Re-test queue — PROD-2026-09-16
Run SERIALLY after the main batch finishes. Concurrency against slow Production
produces false failures (rows=0, addNew timeouts) — one browser at a time.

## A. Drivers that aborted part-way (must re-run to completion)
- [ ] SETTINGS - PRODUCT CATEGORY — aborted on null `.md-dialog--full-page`; 25/45 left Not Tested, 6 Fail suspect
- [ ] SETTINGS - BRAND — aborted on null `.md-dialog--full-page`; 26/56 left Not Tested, 11 Fail suspect
  NOTE: record-shell class on this Production build is still UNCONFIRMED. Probe it
  with one browser, no contention, before re-running. nullnet=.md-dialog--full-page, QA=.advancedFullDialog

- [ ] SETTINGS - REGISTRATION SURVEY — survey_run.py crashed (Locator.click 30s timeout); all 7 scenarios Not Tested
- [ ] SETTINGS - PLAN — 17 Fail / 45 Pass; unusually high fail count, triage before filing

## B. Confirmed harness artifacts — flip to Pass after CRUD re-test
- [ ] SETTINGS - ADMINISTRATORS  New Administrator|5 — record WAS created (verified on reload)
- [ ] SETTINGS - COVERAGE TYPE   Grid|10..14 — record WAS created; CRUD chain cascaded off a stale search

## C. Harness selector mismatch — re-test with correct interaction
- [ ] SETTINGS - REGIONS  New Region|2..5 + Grid|10..14
      "Region Name *" is a react-select (`sel:True`), NOT a plain text input.
      Fill via click -> type -> Enter (setlib.act_input path), not Locator.fill.
      Save & Continue stays disabled until it is set — that is correct behaviour, not a bug.

## D. Still unresolved — needs a clean serial run
- [ ] SETTINGS-REVIEW QUESTIONS  New Review Question|5 + Grid|10..14
      Pass 1: Save & Close enabled, clicked, dialog stayed open, NO error text, no record.
      Must distinguish silent-save-failure (real bug) from unfilled required field
      with no validation message (also a bug, different one). Fill title+question+option.
- [ ] SETTINGS - SUPPORT  Support|14 + Grid|10..14 — same shape as review-questions
- [ ] SETTINGS - DEVICE CATEGORY — triage the 5 Fails (not yet examined)
- [ ] SETTINGS - LANGUAGE Grid|4..14 — determine which are genuinely unreachable
      because of the page-collapse bug vs. independently testable

## E. CONFIRMED REAL DEFECT (verified, reproducible, ready to file)
- Languages settings filter collapses the page.
  Repro: /portal/languages -> "Filter Languages" -> "Select a filter" -> pick "Language".
  Result: body innerText length 0, body innerHTML 116 chars, nav gone, grid gone.
  Recovery: full page reload only. Evidence: evidence/verify/lang_3_afterpick.png
  Matches INSTA-1401 filed against nullnet 2026-08-17 — now reproducing on PRODUCTION.
  Severity High. Blocks Languages Grid|4..14.

## Test records created in Production so far (all deleted unless noted)
RegTest20260916 / VerifyTest0916 / VerifyTwo0916 in: coverage-cost-type, coverage-type,
administrators, underwriters, share, support, review-questions, languages, regions.
All confirmed deleted. VerifyTwo0916 regions create never succeeded (nothing to clean).
