"""Part 3 — final confirmation:
- Verify Company toggle by id is unambiguous.
- Verify SKU toggle by id resolves cleanly after Company select.
- Verify role=option lookup by SKU name returns exactly the right one.
- Verify the close button selector (currently {"role": "button", "name": "close"})
  doesn't conflict with the dialog-title-close button.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(r"C:\Users\sarahgamba\Dropbox\PC\Documents\pm-instaprotek")
STORAGE = REPO / ".claude" / "skills" / "instaprotek-enterprise-registration" / ".auth" / "storage_state.json"
OUT = REPO / "tmp" / "diagnostic"
SAMPLE_XLSX = OUT / "sample_bulk.xlsx"
BASE = "https://qa.crm.instaprotek.com"
HEADLESS = True


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS)
        ctx = browser.new_context(storage_state=str(STORAGE), viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        try:
            page.goto(BASE + "/portal/registration", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            page.get_by_role("button", name="file_upload Import CSV").first.click()
            page.wait_for_timeout(1200)
            page.locator("input[type='file']").first.set_input_files(str(SAMPLE_XLSX))
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="chevron_right Next").first.click()
            page.wait_for_timeout(2500)

            print("=== Counts BEFORE company selected ===")
            print(f"  #company-toggle      count: {page.locator('#company-toggle').count()}")
            print(f"  #register_under-toggle count: {page.locator('#register_under-toggle').count()}")
            print(f"  .bulkDialog [role=listbox] count: {page.locator('.bulkDialog [role=listbox]').count()}")

            print("\n=== Open Company via #company-toggle and click 'Demo Company' ===")
            page.locator("#company-toggle").click()
            page.wait_for_timeout(1000)
            page.wait_for_selector("[role='option']", timeout=8000)
            opts = page.get_by_role("option")
            print(f"  visible options: {opts.count()}")
            demo = page.get_by_role("option", name="Demo Company")
            print(f"  exact 'Demo Company' option count: {demo.count()}")
            demo.first.click()
            page.wait_for_timeout(1200)

            print("\n=== Counts AFTER company selected ===")
            print(f"  #company-toggle      count: {page.locator('#company-toggle').count()}")
            print(f"  #register_under-toggle count: {page.locator('#register_under-toggle').count()}")
            print(f"  .bulkDialog [role=listbox] count: {page.locator('.bulkDialog [role=listbox]').count()}")

            print("\n=== Open SKU via #register_under-toggle ===")
            page.locator("#register_under-toggle").click()
            page.wait_for_timeout(1000)
            page.wait_for_selector("[role='option']", timeout=8000)
            sku_options = page.get_by_role("option")
            print(f"  visible SKU options: {sku_options.count()}")
            for i in range(sku_options.count()):
                t = (sku_options.nth(i).inner_text() or "").strip()
                print(f"    [{i}] {t!r}")

            # Exact-match SKU by name
            sku_target = "ESC030012MO00IK"
            print(f"\n  get_by_role('option', name='{sku_target}') count: {page.get_by_role('option', name=sku_target).count()}")
            print(f"  get_by_role('option', name='{sku_target}', exact=True) count: {page.get_by_role('option', name=sku_target, exact=True).count()}")

            # Probe the option also by another sku to make sure we don't match SKU prefix collisions
            for s in ("846641731777", "614238026266", "814202333330"):
                c = page.get_by_role("option", name=s).count()
                print(f"  option name={s!r} count={c}")

            page.keyboard.press("Escape")
            page.wait_for_timeout(400)

            print("\n=== Close button probe ===")
            # The current selector is {"role": "button", "name": "close"}; the only button
            # in the dialog with text 'close' is the dialog-title-close at top right
            close_count = page.get_by_role("button", name="close").count()
            print(f"  get_by_role('button', name='close') count: {close_count}")
            for i in range(min(close_count, 5)):
                b = page.get_by_role("button", name="close").nth(i)
                info = b.evaluate(
                    r"""(el) => ({text: (el.textContent || '').trim().slice(0,80), classes: el.className, in_dialog: !!el.closest('.bulkDialog')})"""
                )
                print(f"    [{i}] {info}")

            # And the {"role":"button","name":"closeCancel"} variant in case it's the safer choice
            cancel_count = page.get_by_role("button", name="closeCancel").count()
            print(f"  get_by_role('button', name='closeCancel') count: {cancel_count}")

            print("\n>> done")
        except Exception:
            print("!! failed:", traceback.format_exc())
            return 1
        finally:
            time.sleep(1)
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
