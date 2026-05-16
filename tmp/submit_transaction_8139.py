"""Submit New Transaction for batch 8139 in QA CRM.

Reuses the project's CRMRunner — logs in via storage state, navigates to Demo Company →
Extended Service Contract - 12 Months → Batches, opens batch 8139, then drives the
3-tab New Transaction dialog. Uses today's date for both Transaction Date and Effective Date.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = PROJECT_ROOT / ".claude/skills/instaprotek-enterprise-registration"
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from utils import load_credentials, load_json, setup_logger  # noqa: E402
from playwright_runner import CRMRunner, TransactionInput  # noqa: E402


def main() -> int:
    logger = setup_logger(log_file=None, verbose=True)

    settings = load_json(SKILL_DIR / "config/settings.json")
    selectors = load_json(SKILL_DIR / "config/selectors.json")
    creds = load_credentials()
    if creds.crm_base_url:
        settings["crm"]["base_url"] = creds.crm_base_url

    screenshot_dir = PROJECT_ROOT / "tmp/txn_8139_screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    storage = SKILL_DIR / ".auth/storage_state.json"

    today_us = datetime.now().strftime("%m/%d/%Y")
    txn = TransactionInput(transaction_date=today_us, effective_date=today_us)
    logger.info("Submitting transaction for batch 8139 with transaction_date=%s effective_date=%s", today_us, today_us)

    with CRMRunner(
        settings=settings,
        selectors=selectors,
        credentials=creds,
        headless=True,
        screenshot_dir=screenshot_dir,
        storage_state_path=storage,
        logger=logger,
    ) as runner:
        runner.login()
        runner.open_company_and_plan("Demo Company", "Extended Service Contract - 12 Months")

        # Batches tab is part of plan_detail; click via JS and verify aria-selected. The Plan
        # Details modal has an auto-swap behavior (observed Batches → Timeline) so we retry.
        page = runner._page

        def click_batches_tab_js():
            return page.evaluate(
                """() => {
                    const labels = document.querySelectorAll('.md-tab-label');
                    for (const lbl of labels) {
                        if ((lbl.textContent || '').trim().toLowerCase() === 'batches') {
                            const tab = lbl.closest("[role='tab']");
                            if (tab) { tab.click(); return tab.id || 'unknown'; }
                        }
                    }
                    return null;
                }"""
            )

        def batches_active():
            return bool(page.evaluate(
                """() => {
                    const labels = document.querySelectorAll('.md-tab-label');
                    for (const lbl of labels) {
                        if ((lbl.textContent || '').trim().toLowerCase() === 'batches') {
                            const tab = lbl.closest("[role='tab']");
                            return !!(tab && tab.getAttribute('aria-selected') === 'true');
                        }
                    }
                    return false;
                }"""
            ))

        for attempt in range(5):
            clicked_id = click_batches_tab_js()
            logger.info("Batches tab click attempt %d -> id=%r", attempt + 1, clicked_id)
            page.wait_for_timeout(800)
            if batches_active():
                break
        else:
            logger.error("Could not activate Batches tab after 5 attempts")
            page.screenshot(path=str(screenshot_dir / "batches_tab_not_active.png"), full_page=True)
            return 1

        page.screenshot(path=str(screenshot_dir / "batches_tab_active.png"), full_page=True)

        # Wait for table rows to populate; capture batch row by JS in one shot.
        try:
            page.wait_for_selector("table tbody tr", timeout=15000)
        except Exception:
            logger.warning("Batches table didn't populate in 15s")

        # Tag the row whose first cell is "8139" in a single JS call so the locator is stable.
        found = page.evaluate("""() => {
          const rows = Array.from(document.querySelectorAll('table tbody tr'));
          for (const r of rows) {
              const c = r.querySelector('td');
              if (!c) continue;
              if ((c.innerText || '').trim() === '8139') {
                  r.setAttribute('data-tmp-id', '__row_8139__');
                  return true;
              }
          }
          return false;
        }""")
        if not found:
            page.screenshot(path=str(screenshot_dir / "batch_8139_not_found.png"), full_page=True)
            logger.error("Batch 8139 not found in the Batches table")
            return 1

        row_loc = page.locator("table tbody tr[data-tmp-id='__row_8139__'] td").first
        row_loc.click()
        logger.info("Clicked batch 8139 row")

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)  # let batch detail render
        page.screenshot(path=str(screenshot_dir / "batch_8139_opened.png"), full_page=True)

        # Click New Transaction — dialog is 3-step. Every text field is pre-populated;
        # only thing we need to do is select all pins, then Next → Next → Generate.
        from playwright_runner import _locator as _loc2
        new_txn_sel = selectors["batch_detail"]["new_transaction_button"]
        _loc2(page, new_txn_sel).first.click()
        page.wait_for_timeout(3000)
        page.screenshot(path=str(screenshot_dir / "txn_step1_opened.png"), full_page=True)

        # Toggle all pins via Playwright force-click on the header checkbox (#undefined-toggle-all).
        # force=True bypasses actionability checks (hidden inputs that react-md uses).
        def selection_count():
            return page.evaluate("""() => {
              const d = document.querySelector('[role=\"dialog\"], .md-dialog--centered, .userDialog');
              const m = d && d.innerText.match(/Selected Pin\\/s:\\s*(\\d+)\\s*Out Of\\s*(\\d+)/);
              return m ? {selected: +m[1], total: +m[2]} : null;
            }""")

        # Try force-click on header checkbox (most direct path)
        try:
            page.locator("#undefined-toggle-all").first.click(force=True, timeout=5000)
            page.wait_for_timeout(1500)
        except Exception as exc:
            logger.warning("Force-click on toggle-all failed: %s", exc)

        sel_text = selection_count()
        logger.info("After force-click toggle-all: %s", sel_text)

        # If not all selected, iterate any unchecked pin individually with retries until all selected.
        attempt = 0
        while sel_text and sel_text["selected"] < sel_text["total"] and attempt < 6:
            attempt += 1
            unchecked_ids = page.evaluate("""() => {
              const ids = [];
              for (let i = 1; i <= 50; i++) {
                  const cb = document.getElementById('undefined-' + i);
                  if (cb && cb.type === 'checkbox' && !cb.checked) ids.push(cb.id);
              }
              return ids;
            }""")
            logger.info("Attempt %d: %d unchecked pins to click", attempt, len(unchecked_ids))
            for cid in unchecked_ids:
                try:
                    page.locator(f"#{cid}").first.click(force=True, timeout=2000)
                    page.wait_for_timeout(150)
                except Exception:
                    pass
            page.wait_for_timeout(500)
            sel_text = selection_count()
            logger.info("After attempt %d: %s", attempt, sel_text)

        if not sel_text or sel_text["selected"] < sel_text["total"]:
            logger.error("Failed to select all pins: %s", sel_text)
            page.screenshot(path=str(screenshot_dir / "FAILURE_pins_not_all_selected.png"), full_page=True)
            return 1

        logger.info("All %d pins selected", sel_text["total"])
        page.screenshot(path=str(screenshot_dir / "txn_step1_pins_selected.png"), full_page=True)

        # Click Next to step 2
        def click_dialog_button(text: str) -> bool:
            return bool(page.evaluate(
                """(t) => {
                  const d = document.querySelector('[role=\"dialog\"], .md-dialog--centered, .userDialog');
                  if (!d) return false;
                  const btns = Array.from(d.querySelectorAll('button'));
                  const target = btns.reverse().find(b => (b.innerText || '').toLowerCase().includes(t.toLowerCase()) && !b.disabled);
                  if (!target) return false;
                  target.click();
                  return true;
                }""",
                text,
            ))

        # Click Next from the Pins step. The CRM jumps straight to Step 3 (review) — Step 1
        # (Transaction Details) is pre-populated and skipped automatically.
        if not click_dialog_button("Next"):
            logger.error("Could not click Next from Pins step")
            return 1
        page.wait_for_timeout(2000)
        page.screenshot(path=str(screenshot_dir / "txn_step3_review.png"), full_page=True)

        # Step 3: Generate New Transaction
        if not click_dialog_button("Generate"):
            logger.error("Could not click Generate")
            return 1
        page.wait_for_timeout(3000)
        page.screenshot(path=str(screenshot_dir / "txn_after_generate.png"), full_page=True)

        # Wait for success message
        try:
            page.wait_for_function(
                """() => {
                  return /Transaction successfully generated/i.test(document.body.innerText) ||
                         /Transaction Submitted/i.test(document.body.innerText) ||
                         /successfully/i.test(document.body.innerText);
                }""",
                timeout=60000,
            )
            page.screenshot(path=str(screenshot_dir / "txn_success.png"), full_page=True)
            logger.info("Transaction successfully submitted for batch 8139")
            return 0
        except Exception as exc:
            page.screenshot(path=str(screenshot_dir / "txn_no_success_indicator.png"), full_page=True)
            logger.warning("Did not detect success indicator within 60s: %s", exc)
            return 2


if __name__ == "__main__":
    sys.exit(main())
