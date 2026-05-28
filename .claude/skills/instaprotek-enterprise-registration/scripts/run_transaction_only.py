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
    p.add_argument("--pin-count", type=int, default=None, help="Expected pin count for verification (e.g. 75)")
    p.add_argument("--prod-dialog", action="store_true",
                   help="Use the prod New Transaction dialog flow (Tab 1=metadata, Tab 2=pins paginated, Tab 3=generate).")
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
        if args.prod_dialog:
            contract_numbers = _create_transaction_prod(
                runner, args.transaction_date, args.effective_date, args.pin_count, logger, screenshot_dir,
            )
            logger.info("Transaction generated. %d contract number(s) captured.", len(contract_numbers))
            for c in contract_numbers[:5]:
                logger.info("  contract: %s", c)
            if len(contract_numbers) > 5:
                logger.info("  ... (%d more)", len(contract_numbers) - 5)
            print("\nCONTRACT_NUMBERS:" + ",".join(contract_numbers))
        else:
            runner.create_transaction(TransactionInput(
                transaction_date=args.transaction_date,
                effective_date=args.effective_date,
            ))
        logger.info("Transaction step completed for PO %s", args.po)
    return 0


def _create_transaction_prod(runner, transaction_date: str, effective_date: str,
                              pin_count: int | None, logger, screenshot_dir: Path) -> list[str]:
    """Drive the prod New Transaction dialog and return the resulting contract numbers.

    Prod dialog layout (different from QA):
      Tab 1 — Transaction Details: dates (pre-filled to PO order date), SKU, qty, price,
              sales order, channel. Override Effective Date if needed, then click Next.
      Tab 2 — Pin selection table (paginated). Set Rows per page to 100, then header
              select-all checkbox, then Next.
      Tab 3 — Review. Click Generate New Transaction. Wait for success alert.
    After success, navigate to the batch detail's Contracts tab and scrape the contract
    numbers from the first column.
    """
    from playwright_runner import _react_set_input, _react_close_datepicker, _shot
    page = runner._page

    # Click New Transaction button on the batch detail page.
    new_txn_btn = page.get_by_role("button", name="s New Transaction").first
    try:
        new_txn_btn.click(timeout=10000)
    except Exception:
        page.locator("button:has-text('New Transaction')").first.click()
    page.wait_for_timeout(800)
    _shot(page, screenshot_dir, "prod_txn_tab1_opened")

    # Tab 1 — override Effective Date (Transaction Date is already PO order date).
    eff_date_css = "[role='dialog'] .react-datepicker-component:nth-of-type(2) input"
    try:
        _react_set_input(page, eff_date_css, effective_date)
        _react_close_datepicker(page, eff_date_css)
    except Exception as exc:
        logger.warning("Could not override Effective Date (%s); using dialog default: %s", effective_date, exc)
    _shot(page, screenshot_dir, "prod_txn_tab1_effective_date_set")

    # Click Next -> Tab 2.
    page.get_by_role("button", name="chevron_right Next").first.click()
    page.wait_for_timeout(1000)
    _shot(page, screenshot_dir, "prod_txn_tab2_opened")

    # Tab 2 — change Rows per page to 100 so all pins are visible on one page.
    _set_rows_per_page_100(page, logger)
    _shot(page, screenshot_dir, "prod_txn_tab2_rows_per_page_attempted")

    import re as _re

    def _selected() -> tuple[int, int] | None:
        try:
            txt = page.locator("[role='dialog']").first.inner_text(timeout=1000)
        except Exception:
            return None
        m = _re.search(r"Selected Pin/s:\s*(\d+)\s*Out Of\s*(\d+)", txt)
        return (int(m.group(1)), int(m.group(2))) if m else None

    # Click header select-all.
    clicked = page.evaluate("""() => {
        const d = document.querySelector('[role="dialog"]');
        if (!d) return false;
        const cb = d.querySelector('input[type="checkbox"]');
        if (!cb) return false;
        if (!cb.checked) cb.click();
        return true;
    }""")
    if not clicked:
        _shot(page, screenshot_dir, "prod_txn_tab2_FAILURE_no_checkbox")
        raise RuntimeError("Could not find select-all checkbox in transaction dialog Tab 2")

    # Give the dialog time to update the count, then check.
    page.wait_for_timeout(1500)
    c = _selected()
    logger.info("After header select-all: %s", c)

    target_total = pin_count if pin_count is not None else (c[1] if c else 0)

    if c is None or c[0] < c[1]:
        logger.info("Not all pins selected (have %s). Falling back to paginated select-all.", c)
        _paginated_select_all(page, logger, screenshot_dir, target_total)
        c = _selected()
        logger.info("After paginated select-all: %s", c)

    if c is None or c[0] != c[1] or (pin_count is not None and c[0] != pin_count):
        _shot(page, screenshot_dir, f"prod_txn_tab2_FAILURE_pin_count_mismatch")
        raise RuntimeError(f"Pin selection did not reach total. State: {c}, expected={pin_count}")
    _shot(page, screenshot_dir, "prod_txn_tab2_pins_selected")

    # Click Next -> Tab 3.
    page.get_by_role("button", name="chevron_right Next").first.click()
    page.wait_for_timeout(1000)
    _shot(page, screenshot_dir, "prod_txn_tab3_opened")

    # Click Generate New Transaction.
    gen = page.get_by_role("button", name="check Generate New Transaction").first
    try:
        gen.click(timeout=8000)
    except Exception:
        page.locator("button:has-text('Generate New Transaction')").first.click()

    # Wait for success alert/text.
    page.get_by_text("Transaction successfully generated.", exact=False).first.wait_for(
        state="visible", timeout=120_000,
    )
    _shot(page, screenshot_dir, "prod_txn_generated")

    # Dialog auto-closes (or we close it). Wait until we're back on batch detail.
    page.wait_for_timeout(1500)

    # Scrape contract numbers from the Contracts tab on the batch.
    return _scrape_contract_numbers(page, logger, screenshot_dir)


def _set_rows_per_page_100(page, logger) -> None:
    """Change the dialog's pin-table 'Rows per page' to 100.

    The pagination control sits at the bottom of the pin table, below the dialog's
    visible viewport — must scroll it into view first. Strategy:
      1. Find any element with text matching "Rows per page" inside the dialog.
      2. scroll_into_view_if_needed() so the control is interactable.
      3. Click the sibling listbox/toggle showing the current page-size value (5/10/25/50).
      4. Click the "100" option from the opened menu.
    """
    dialog = page.locator("[role='dialog']").first

    # Native <select> short-circuit.
    try:
        select = dialog.locator("select").first
        if select.count() > 0 and select.is_visible(timeout=500):
            select.select_option("100")
            logger.info("Rows per page set to 100 via native <select>")
            return
    except Exception:
        pass

    # Scroll the dialog's internal scroll container to the bottom so the pagination row
    # comes into view. Playwright's auto-scroll doesn't always traverse nested scroll
    # containers correctly — JS scroll is more reliable.
    try:
        page.evaluate("""() => {
            const d = document.querySelector('[role="dialog"]');
            if (!d) return;
            const candidates = [d, ...d.querySelectorAll('*')];
            for (const el of candidates) {
                if (el.scrollHeight > el.clientHeight) {
                    el.scrollTop = el.scrollHeight;
                }
            }
        }""")
        page.wait_for_timeout(400)
    except Exception as exc:
        logger.warning("JS scroll inside dialog failed: %s", exc)

    # Find the page-size listbox: look for a [role='listbox'] near the "Rows per page" label
    # whose visible value is one of 5/10/25/50/100.
    try:
        listboxes = dialog.locator("[role='listbox']")
        n = listboxes.count()
        logger.info("Found %d listbox(es) in dialog while changing rows-per-page", n)
        for i in range(n):
            t = listboxes.nth(i)
            try:
                label = (t.inner_text(timeout=1000) or "").strip()
            except Exception:
                continue
            logger.info("  listbox[%d] text=%r", i, label[:40])
            # Listbox text often includes an icon name suffix like "\narrow_drop_down" —
            # take the first non-empty line and compare that.
            first_line = label.split("\n")[0].strip() if label else ""
            if first_line in {"5", "10", "25", "50", "100"}:
                # The pagination toggle has id="undefined-pagination-toggle" and sits below
                # the dialog's visible viewport. Playwright's auto-scroll + force-click both
                # fail with "outside of the viewport" because of nested scrolling. Click via
                # raw JS (which doesn't care about viewport).
                opened = page.evaluate("""() => {
                    const d = document.querySelector('[role="dialog"]');
                    if (!d) return 'no-dialog';
                    const toggle = d.querySelector('[role="listbox"].md-select-field--pagination, [role="listbox"][id*="pagination-toggle"]');
                    if (!toggle) return 'no-toggle';
                    toggle.scrollIntoView({block: 'center'});
                    toggle.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    toggle.click();
                    return 'opened';
                }""")
                logger.info("Pagination toggle click via JS: %s", opened)
                page.wait_for_timeout(600)
                # The 100 option is rendered in a document-level portal at coordinates
                # outside the dialog's viewport. Click it via JS too.
                picked = page.evaluate("""() => {
                    const opts = Array.from(document.querySelectorAll('[role="option"]'));
                    const target = opts.find(o => o.getAttribute('data-value') === '100')
                        || opts.find(o => (o.textContent || '').trim().startsWith('100'));
                    if (!target) return 'no-option';
                    target.scrollIntoView({block: 'center'});
                    target.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    target.click();
                    return 'clicked';
                }""")
                logger.info("100-option click via JS: %s", picked)
                page.wait_for_timeout(1500)
                return
    except Exception as exc:
        logger.warning("Rows-per-page change via listbox failed: %s", exc)

    logger.warning("Could not change Rows per page to 100 — will fall back to paginated select-all.")


def _paginated_select_all(page, logger, screenshot_dir: Path, expected_total: int) -> None:
    """Fallback when rows-per-page change failed: click select-all on each page, then Next page.

    Continues until 'Selected Pin/s: N Out Of M' satisfies N == M == expected_total or
    pagination runs out.
    """
    from playwright_runner import _shot
    import re as _re

    def _selected_count() -> tuple[int, int] | None:
        try:
            txt = page.locator("[role='dialog']").first.inner_text(timeout=1000)
        except Exception:
            return None
        m = _re.search(r"Selected Pin/s:\s*(\d+)\s*Out Of\s*(\d+)", txt)
        return (int(m.group(1)), int(m.group(2))) if m else None

    safety = 20
    iteration = 0
    while iteration < safety:
        iteration += 1
        # Click select-all on the current page via JS.
        page.evaluate("""() => {
            const d = document.querySelector('[role="dialog"]');
            const cb = d && d.querySelector('input[type="checkbox"]');
            if (cb && !cb.checked) cb.click();
            return !!cb;
        }""")
        page.wait_for_timeout(800)
        c = _selected_count()
        logger.info("Page %d: selected=%s", iteration, c)
        if c and c[0] >= c[1]:
            return
        # Try next page.
        next_btn = page.locator("[role='dialog'] button:has-text('keyboard_arrow_right')").first
        try:
            if not next_btn.is_visible(timeout=1000) or not next_btn.is_enabled(timeout=1000):
                _shot(page, screenshot_dir, f"paginated_select_all_done_iter_{iteration}")
                return
            next_btn.click()
            page.wait_for_timeout(800)
        except Exception:
            _shot(page, screenshot_dir, f"paginated_select_all_no_next_iter_{iteration}")
            return


def _scrape_contract_numbers(page, logger, screenshot_dir: Path) -> list[str]:
    """After a transaction success, scrape Contract Numbers from the batch's Contracts tab.

    The batch detail page has tabs: Details / Pins / Contracts / Timeline / Notes. The
    Contracts tab lists each generated contract with a Contract Number column (usually
    cell index 0 or 1). If pagination is present, scroll/paginate; for now we bump rows
    per page to a large value and read the visible page.
    """
    from playwright_runner import _shot

    # Click the Contracts tab.
    try:
        page.get_by_role("tab", name="s Contracts").first.click(timeout=10000)
    except Exception:
        try:
            page.locator("li[role='tab']:has-text('Contracts')").first.click()
        except Exception:
            logger.warning("Could not click Contracts tab — returning empty contract list")
            _shot(page, screenshot_dir, "contracts_tab_click_failed")
            return []

    page.wait_for_timeout(1000)
    # Wait for any loading overlay to clear.
    try:
        page.wait_for_function(
            """() => !Array.from(document.querySelectorAll('*')).some(
                el => el.children.length === 0 && (el.textContent || '').trim() === 'Getting Records...'
            )""",
            timeout=30000,
        )
    except Exception:
        pass

    # Bump rows per page so all contracts fit on one screen.
    try:
        _set_rows_per_page_100(page, logger)
        page.wait_for_timeout(800)
    except Exception:
        pass

    _shot(page, screenshot_dir, "contracts_tab_loaded")

    numbers: list[str] = []
    rows = page.get_by_role("row")
    n = rows.count()
    # Heuristic: try cells 0 and 1 — the first non-empty cell with a contract-looking value wins.
    import re as _re
    contract_re = _re.compile(r"^[A-Z0-9-]{6,}$")
    for i in range(n):
        row = rows.nth(i)
        cells = row.get_by_role("cell")
        if cells.count() == 0:
            continue
        for c in range(min(2, cells.count())):
            txt = (cells.nth(c).inner_text() or "").strip()
            if txt and contract_re.match(txt) and "rows per page" not in txt.lower():
                numbers.append(txt)
                break

    # Dedupe while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for x in numbers:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    logger.info("Scraped %d contract number(s) from Contracts tab", len(ordered))
    return ordered


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
