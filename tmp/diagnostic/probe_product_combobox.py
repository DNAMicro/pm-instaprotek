"""Confirm: clicking the product_name combobox opens an options menu, and verify
how to select the only option."""
from __future__ import annotations
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(r"C:\Users\sarahgamba\Dropbox\PC\Documents\pm-instaprotek")
STORAGE = REPO / ".claude" / "skills" / "instaprotek-enterprise-registration" / ".auth" / "storage_state.json"
OUT = REPO / "tmp" / "diagnostic"


def shot(page, name):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context(storage_state=str(STORAGE), viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.goto("https://qa.crm.instaprotek.com/portal/company", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.get_by_role("textbox", name="Search Companies...").fill("Demo Company")
        page.wait_for_timeout(1200)
        page.get_by_role("cell", name="Demo Company").first.click()
        page.wait_for_timeout(1500)
        page.get_by_role("tab", name="i Plans").click()
        page.wait_for_timeout(1500)
        page.get_by_role("cell", name="Extended Service Contract - 12 Months").first.click()
        page.wait_for_timeout(1500)
        page.get_by_role("tab", name="s Batches").click()
        page.wait_for_timeout(1500)
        page.locator(".advancedFullDialog").first.get_by_role("button", name="add New").first.click()
        page.wait_for_timeout(2000)
        shot(page, "30_dialog_before_combobox_click")

        # The Select-arrow lives next to the Product input. Click the Product container.
        print("Clicking the .Select-control containing #product_name ...")
        page.evaluate("""() => {
          const inp = document.getElementById('product_name');
          if (!inp) return false;
          const ctrl = inp.closest('.Select-control') || inp.closest('.Select') || inp.parentElement;
          ctrl.click();
          return true;
        }""")
        page.wait_for_timeout(1000)
        shot(page, "31_after_combobox_click")

        # See what options exist now
        opts = page.evaluate("""() => {
          const opts = Array.from(document.querySelectorAll('[role="option"], .Select-option'));
          return opts.map(o => ({
            role: o.getAttribute('role'),
            classes: o.className,
            text: (o.textContent || '').trim().slice(0,120),
            visible: o.getBoundingClientRect().width > 0,
          }));
        }""")
        print(f"\nOptions found: {len(opts)}")
        for o in opts:
            print(f"  {o}")

        # try get_by_role('option') count
        cnt = page.get_by_role("option").count()
        print(f"\nplaywright get_by_role('option') count: {cnt}")
        for i in range(min(cnt, 8)):
            o = page.get_by_role("option").nth(i)
            try:
                print(f"  opt[{i}] visible={o.is_visible()} text={o.inner_text()[:80]!r}")
            except Exception as e:
                print(f"  opt[{i}] err {e}")

        # try the alternative: click via the input directly (Playwright)
        print("\n--- Closing dialog and re-opening to try input.click() ---")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        page.locator(".advancedFullDialog").first.get_by_role("button", name="add New").first.click()
        page.wait_for_timeout(1500)

        try:
            page.locator("#product_name").click()
            page.wait_for_timeout(800)
            shot(page, "32_input_clicked")
            cnt2 = page.get_by_role("option").count()
            print(f"After #product_name click: option count={cnt2}")
        except Exception as e:
            print(f"input click failed: {e}")

        # Also test the new selector strategy: combobox by id 'product_name'
        print("\n--- Test locator('.Select-control'):has(#product_name) ---")
        try:
            ctrl_count = page.locator(".Select-control:has(#product_name)").count()
            print(f"  count = {ctrl_count}")
        except Exception as e:
            print(f"  err: {e}")

        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
