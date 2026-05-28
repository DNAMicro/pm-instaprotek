"""One-shot: run only Step 4 (New Transaction) against an existing prod batch.

Use when the batch + bulk upload were completed manually (or by a prior interrupted run)
and only the transaction step remains. Reuses the persisted storage state for login.

Usage:
    python .claude/skills/instaprotek-enterprise-registration/scripts/run_transaction_only.py \
        --env Production --company "Connected Solutions Group, LLC" \
        --plan "Extended Service Contract - 12 Months" --po 42325 \
        --transaction-date 05/27/2026 --effective-date 05/19/2026 --headed
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from utils import AUTH_DIR, CONFIG_DIR, PROCESSED_DIR, load_credentials, load_json, setup_logger, utc_timestamp


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--env", default=None)
    p.add_argument("--company", required=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--po", required=True)
    p.add_argument("--transaction-date", required=True, help="MM/DD/YYYY")
    p.add_argument("--effective-date", required=True, help="MM/DD/YYYY")
    p.add_argument("--headed", action="store_true")
    args = p.parse_args()

    logger = setup_logger(log_file=None, verbose=True)
    settings = load_json(CONFIG_DIR / "settings.json")
    credentials = load_credentials(env=args.env)
    if credentials.crm_base_url:
        settings.setdefault("crm", {})["base_url"] = credentials.crm_base_url

    selectors = load_json(CONFIG_DIR / "selectors.json")
    storage_state_path = AUTH_DIR / "storage_state.json"
    run_ts = utc_timestamp()
    screenshot_dir = PROCESSED_DIR / f"{run_ts}_PO{args.po}_txn_only" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    from playwright_runner import CRMRunner, TransactionInput, _shot

    with CRMRunner(
        settings=settings,
        selectors=selectors,
        credentials=credentials,
        headless=not args.headed,
        screenshot_dir=screenshot_dir,
        storage_state_path=storage_state_path,
        logger=logger,
    ) as runner:
        runner.login()
        runner.open_company_and_plan(args.company, args.plan)
        _open_batch_via_search(runner, args.po, logger, screenshot_dir)
        runner.create_transaction(TransactionInput(
            transaction_date=args.transaction_date,
            effective_date=args.effective_date,
        ))
        logger.info("Transaction step completed for PO %s", args.po)
    return 0


def _open_batch_via_search(runner, po_number: str, logger, screenshot_dir: Path) -> None:
    """Wait for the Batches table to load, type the PO into Search Batches, click first row."""
    from playwright_runner import _shot
    page = runner._page

    # Click the Batches tab inside the Plan Details modal.
    batches_tab = page.get_by_role("tab", name="s Batches").first
    try:
        batches_tab.click(timeout=10000)
    except Exception:
        page.locator("li[role='tab']:has-text('Batches')").first.click()
    page.wait_for_timeout(500)
    _shot(page, screenshot_dir, "batches_tab_clicked")

    # Wait for the "Getting Records..." overlay to disappear.
    try:
        page.wait_for_function(
            """() => {
                return !Array.from(document.querySelectorAll('*')).some(
                    el => el.children.length === 0
                        && (el.textContent || '').trim() === 'Getting Records...'
                );
            }""",
            timeout=30000,
        )
    except Exception:
        logger.warning("'Getting Records...' overlay still present after 30s")

    page.wait_for_timeout(500)
    _shot(page, screenshot_dir, "batches_table_loaded")

    # Type the PO into Search Batches input.
    search = page.get_by_role("textbox", name="Search Batches...").first
    search.wait_for(state="visible", timeout=10000)
    search.fill("")
    search.fill(po_number)
    page.wait_for_timeout(1500)  # debounce + server filter
    try:
        page.wait_for_function(
            """() => {
                return !Array.from(document.querySelectorAll('*')).some(
                    el => el.children.length === 0
                        && (el.textContent || '').trim() === 'Getting Records...'
                );
            }""",
            timeout=15000,
        )
    except Exception:
        pass
    _shot(page, screenshot_dir, f"batches_filtered_{po_number}")

    # Click the first data row's first cell.
    rows = page.get_by_role("row")
    n = rows.count()
    logger.info("After filter for PO %s: %d rows present (incl. header)", po_number, n)
    for i in range(n):
        row = rows.nth(i)
        cells = row.get_by_role("cell")
        if cells.count() >= 1:
            txt = (cells.nth(0).inner_text() or "").strip()
            if txt and "rows per page" not in txt.lower():
                logger.info("Clicking batch row: %r", txt)
                cells.nth(0).click()
                _shot(page, screenshot_dir, f"batch_opened_po_{po_number}")
                return
    _shot(page, screenshot_dir, f"FAILURE_no_batch_rows_after_filter_{po_number}")
    raise RuntimeError(f"No data rows in Batches table after filtering for PO {po_number!r}")


if __name__ == "__main__":
    sys.exit(main())
