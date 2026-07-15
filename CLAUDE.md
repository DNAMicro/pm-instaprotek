# CLAUDE.md — pm-instaprotek

Product-management workspace for the Instaprotek portal. The regression-testing kit lives in
`Insta-testing/` (which has its own `CLAUDE.md` with kit-specific detail). The defaults below
apply across the whole project.

## Defaults

- **Default test environment:** `QA-environment`. Use Staging for the final pre-go-live pass and
  Production for smoke checks only.

## Operating instructions

- **Optimize token usage:** match the model to the task — a fast, lightweight model for mechanical
  work (copying templates, filling status cells, tallying counts, simple lookups); a stronger model
  for judgment-heavy work (triaging defect severity, interpreting failures, writing the
  release-readiness / Go–No-go summary).
- **Version control (required):** ALWAYS commit and push at the end of every work cycle — never skip
  it. Run git through **bash** (git is on the bash PATH here, not PowerShell):
  `git add -A && git commit -m "<message>" && git push`.
  Remote: `https://github.com/DNAMicro/pm-instaprotek.git`.
- **Test data cleanup:** after running tests, delete the test records created during the run so the
  environment is left clean. Capture any needed evidence first; never run cleanup against Production.

## Secrets

- `credentials.json` is git-ignored and must never be committed.
