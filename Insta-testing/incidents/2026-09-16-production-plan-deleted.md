# INCIDENT — Production plan record deleted by regression run (2026-09-16)

**Severity:** High — irreversible loss of one live Product Plan record on `crm.instaprotek.com`.
**Caused by:** the regression harness (`tmp/run-2026-09-16/run_plan.py`), not by a product defect.
**Status:** NOT recovered. Requires a database restore.

## The record

| Field | Value | Source |
|---|---|---|
| Record id | `d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a` | driver log `[ctx] recovered plan record` |
| URL | `/portal/product-plans/d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a` | now returns "No records found!" |
| Plan Name | `2 - Years Warranty Replacement` | grid row + Timeline |
| Coverage Amount | `9.16` (displayed `USD 9.16`) | Timeline "Update Plan" 11:49 AM |
| Region | `United States` | grid row |
| Coverage Period | `2` | grid row |
| Terms | PDF beginning `Terms and Cond…` (truncated at capture) | grid row |
| Plan Code, SKU, Administrator, Underwriter, Support, Coverage Type, Coverage Cost Type, Coverage Type Amount, Channel | **UNRECOVERED** | never captured before deletion |

Post-deletion CSV export (`evidence/recover/plans_export.csv`) has 53 rows and does **not**
contain the record — this was a hard delete, not a soft delete. No sibling plan in the
remaining 53 shares the "N - Years Warranty Replacement" naming, so the missing commercial
fields cannot be inferred safely.

## Audit trail (portal Timeline, /portal/timeline)

- `11:49 AM  Update Plan     Name:2 - Years Warranty Replacement  Coverage Amount:9.16  Formatted Coverage Amount:USD 9.16`
- `11:53 AM  Remove Company  Name:2 - Years Warranty Replacement`   <- the deletion

The portal logs the delete under the action name **"Remove Company"**. There is no
"Delete Plan" action value in the Timeline filter.

## What the harness did to the record before deleting it

1. Opened it (believing it was the test record it had just created).
2. Attempted to overwrite a text field with `RegressionTest0916-EDIT` — the fill FAILED, so no
   field value was changed by us.
3. Clicked **Save and Close** -> logged as `Update Plan` at 11:49 AM.
4. Re-opened, attempted `RegressionTest0916-DET`, fill FAILED again, clicked **Save and Close**.
5. **Created a note on the live record** titled `RegressionTest Note Sep16`, then edited and
   re-saved it (scenarios Notes|1-7 all "PASS" — they passed against real data).
6. Teardown clicked **Delete** -> record destroyed at 11:53 AM.

## Root cause

`run_plan.py` creates a test plan, then runs record/edit/delete scenarios against it.
Plan creation FAILED validation (`Plan Name *`, `Coverage Amount *`, `Terms is required`), so
`plan_url` was `None`. The driver then ran its **recovery path**: search the grid for the tag
`RegressionTest0916` and open the first matching row.

**The Plans grid search does not filter.** Verified independently: searching
`RegressionTest0916` on `/portal/product-plans` returns the same 50 rows as any other term.
`N.search_grid()` therefore returned a positive row count, the driver opened row 1 — a real
production plan — and every subsequent scenario, including teardown's delete, targeted it.

Two compounding faults, both in the harness:
1. The recovery path trusts a row count instead of verifying the opened record is ours.
2. `teardown()` deletes whatever `plan_url` points at, with no ownership assertion.

## Fix applied to the harness

An ownership guard (`assert_ours`) now precedes every edit, save and delete: the open record's
text must contain the run tag `RegressionTest0916`, or the operation aborts and the scenario is
recorded Blocked. The grid-search recovery path is removed entirely.

## Blast radius (measured 2026-09-16, read-only)

**289 registrations reference this plan.** Measured via the Registrations grid filter
(`Plan` column -> value `2 - Years Warranty Replacement`): `1-50 of 289`.

The plan value is **still offered as a filter value** on the Registrations grid, and opening a
sample registration (`9d5efa0f-c54f-4237-b044-492767daa709`, registration `680399676351`,
customer Azzaria Carcamo, Superior Communications) shows field `service_plan` still reading
`2 - Years Warranty Replacement`. No error indicators on the record.

So the registrations are **not visibly broken** — they retain the plan value, whether as a
denormalized name snapshot or via a DB row that survives the portal-level delete.

What IS lost: the plan is gone from the Plans catalogue, so
- no NEW registration can be created against it, and
- anything that re-resolves the plan by id at runtime (coverage terms, T&C PDF, claim pricing)
  may fail for those 289 registrations. **This could not be verified from the portal** and should
  be checked at the database/API level.

## Archive investigation (2026-09-17) — is it archived rather than deleted?

PM states the system archives rather than hard-deletes, and that archived records are
retrievable. **Nothing reachable from an Agent-role login brings this record back:**

| Check | Result |
|---|---|
| Record URL direct | "No records found!" |
| Plans grid filter -> Status column | **Does not exist** — typing "stat" matches none of the 14 filter columns |
| CSV export | 53 rows, record absent |
| Routes `?archived=true`, `/archived`, `/archive`, `?status=archived`, `?isActive=false` | all return the same 53 |
| App's own API `POST /node/grid`, `status` field rewritten in-flight to `archived`/`Archived`/`inactive`/`Inactive`/`deleted`/`all`/`0`/`1` | **every value returns exactly 53; the plan is in none** |

The grid payload is `{"start":0,"limit":50,"status":"","sort_column":"name","sort_direction":"asc","node":"product_list","product_company_id":"","grid":true}` — the backend does carry a
`status` concept, but no value tried surfaces the record. Record endpoint is
`GET /node/product_list/<id>`; for this id it returns the SPA shell, not record JSON.

**IMPORTANT DISTINCTION — the delete did not come from the grid.** Teardown opened the record
and clicked the **Delete button inside the open record**, then confirmed Yes. If archive-on-delete
is implemented on the grid's delete icon, the in-record Delete may be a separate code path that
hard-deletes. If confirmed, that is a product defect in its own right and should be filed.

**Caveats on the "unrecoverable" conclusion:**
1. This run is authenticated as `agentqa@dnamicro.com`, **Agent role only** — an admin account
   may expose an archive view not visible here.
2. Only UI + its API were observable. A soft-delete column could exist in the database with
   nothing surfacing it.

**To settle it:** query the product plans table for `d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a` and
inspect its deleted/archived/active column. If the row exists with an archive flag, this is an
un-archive, not a restore.

## Remediation required (cannot be done from the portal)

Restore row `d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a` in the product plans table from the most
recent backup taken before **2026-09-16 11:53 AM America/Phoenix** (18:53 UTC), preserving the
original id so that any registrations/orders referencing it are re-linked.

Also delete the orphaned note `RegressionTest Note Sep16` if the restore brings it back.

## Related

The Timeline also shows `Update Plan  Company Name:RegressionTest0817-DET` — confirming the
2026-08-17 "nullnet" cycle wrote to this same dataset, consistent with the standing note that
`crm.nullnet.instaprotek.com` carries live production data.
