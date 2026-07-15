# Instaprotek Regression Testing — Setup Recap

_Saved 15 Jul 2026. A durable copy of what we set up and what's next, so nothing gets lost even if this chat does._

## What's in this folder (PM-Instaprotek / Insta-testing)

- **Instaprotek_Regression_Test_Plan.docx** — standing plan (scope, approach, environments, criteria, sign-off).
- **Instaprotek_Regression_Tracker.xlsx** — 44 starter test cases + Defect Log + auto-calculating Run Summary.
- **Instaprotek_Pre-Release_Checklist.docx** — pre-ship gate.
- **CLAUDE.md** — standing instructions for this folder.
- **instaprotek-regression-testing.skill** — installable skill bundle (SKILL.md + the three templates).
- **install-skill.ps1** — one-click installer for Claude Code.

## Skill install status

- **Cowork (desktop app):** installed and live — triggers on phrases like "start an Instaprotek regression run", or invoke `/instaprotek-regression-testing`.
- **Claude Code (terminal):** installed as a **project skill** at `C:\Users\sarahgamba\Dropbox\PC\Documents\pm-instaprotek\.claude\skills\instaprotek-regression-testing\` via `install-skill.ps1` (which also removes any personal-scope copy). Restart Claude Code to load it.
- **Manual reinstall in Cowork:** Settings → Capabilities (enable code execution) → Customize → Skills → upload the `.skill` (rename a copy to `.zip` if the uploader asks for a zip).

## Standing defaults (also in CLAUDE.md)

- **Default environment:** QA-environment (Staging for the final pre-go-live pass, Production for smoke only).
- **Token usage:** lightweight model for mechanical steps, stronger model for judgment calls.
- **Version control:** after each cycle, commit and push to git.
- **Test data cleanup:** after a run, delete the test records created during it (never in Production).

## Execution plan we agreed

- **Claude drives the QA portal in Chrome** to run the UI test cases.
- **Sarah imports her own test cases** into the tracker (replacing the generic starters).

## Prep checklist for the browser run

**Login blockers (sort these first):**
- Role accounts: admin, standard, restricted.
- MFA/2FA off on test accounts, or someone available to enter codes (Claude can't receive OTPs).
- SSO: a test IdP account or a local non-SSO login.
- CAPTCHA disabled in QA.
- VPN/network access if the QA URL is internal-only.

**Environment:** correct build deployed to QA and stable; confirmed QA, not Production.

**Test data & assets:** some existing records to act on; sample upload files (normal, oversized, disallowed type); a viewable test inbox (shared mailbox/Mailtrap) for reset & notification cases.

**Scope & rules:** the release/version being tested; which modules to run or skip; OK to create/delete data; third-party integrations in sandbox/test mode.

**Evidence:** screenshots for failures only, or for every case → save to an evidence subfolder.

**Access:** QA portal URL + dedicated test login; Chrome open with the **Claude for Chrome** extension connected.

## Next steps

1. Sarah drops her test-case file into this folder (Excel/CSV/Word) → Claude imports it into the tracker.
2. Sarah lines up portal access + the Chrome connection per the checklist above.
3. Claude runs the suite in batches: records Pass/Fail with notes, logs defects, updates the Run Summary.
4. Clean up test data; commit and push.
