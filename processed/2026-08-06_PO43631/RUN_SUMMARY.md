# PO 43631 — InstaProtek enterprise registration (Production)

**Date:** 2026-08-06 · **Env:** Production (`crm.instaprotek.com`) · **Result:** completed

| Field | Value |
|---|---|
| Company | Connected Solutions Group, LLC |
| Plan | Extended Service Contract - 12 Months |
| Product SKU | ESC030012MO00IK |
| Batch | 9572 |
| PO | 43631 (order date 2026-08-06, qty 15, rate USD 14.43) |
| End user | Erick Betancourt / Kingdom LGX LLC |
| Device | Samsung Galaxy A15 5G ×15 |
| Registrations | 15/15 uploaded, no duplicates (verified by serial search) |
| Used pins | 15 / 15 |
| Transaction date | 08/06/2026 |
| Effective date | 08/03/2026 |
| Contracts | 15 — see `contract_numbers.txt` |
| RingCentral | success posted, HTTP 200 `{"status":"OK"}` |

## Issues hit during this run

1. **Company name has no trailing period.** `"Connected Solutions Group, LLC."` fails with
   `Company ... not found in CRM Company list`. The live prod list reads
   `Connected Solutions Group, LLC`. `SKILL.md` documents the version with the period —
   that is wrong and should be corrected.

2. **Bulk upload rejects Purchase Date >= Delivery Date.** Step 2 flagged all 15 rows with
   `Purchase Date should be less than Delivery Date`. As delivered, the file had
   Delivery Date = 2026-03-08 and Purchase Date = 7/28/2026, which the CRM refuses.
   Delivery Date was set to 2026-08-03 (operator-confirmed) so Jul 28 < Aug 3 passes.
   The Step 2 grid renders dates **MM/DD/YYYY**; the batch form labels its own date field
   `(mm/dd/yyyy)`. Worth adding a pre-flight check for this rule in `validate_inputs.py`
   so it fails before a batch is created.

3. **`run.py` cannot complete a Production transaction.** `CRMRunner.create_transaction`
   drives the QA dialog layout and hangs at the pin-selection wait
   (`wait_for_function: Timeout 15000ms`) — same failure as PO 42322 in May. The transaction
   was completed with `run_transaction_only.py --prod-dialog`, which sets Rows per page to 100
   before select-all (confirmed `(15, 15)`) and scrapes the Contracts tab.
   Porting that logic into `create_transaction` behind an env check would make a prod run
   single-invocation and let the success webhook fire with contract numbers automatically.

4. **Unexplained:** the Step 2 row error-marker also carried `data-tooltip="No pins available"`
   on every row even though batch 9572 had 15 unused pins and
   `use_for_registration` was checked. It did not block the upload once the date error cleared.

## Files

- `43631 instaProtek LLC.xlsx` — file as uploaded (Delivery Date 2026-08-03)
- `43631 instaProtek LLC.original.xlsx` — pristine as-delivered file (Delivery Date 2026-03-08)
- `contract_numbers.txt` — the 15 generated contract numbers
- `run_log_batch_and_upload.txt`, `run_log_transaction.txt`, `screenshots/`, `validation_report.json`, `webhook_response.json`
