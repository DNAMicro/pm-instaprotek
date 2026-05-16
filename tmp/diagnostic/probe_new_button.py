"""Diagnostic probe for the broken "+ New" button on Plan Details > Batches.

Logs all buttons inside .advancedFullDialog with their accessible names, visibility,
disabled state, bounding box, and DOM path. Then clicks the green "+ New" button
several different ways and reports what (if anything) appears in the DOM afterward.

Run:
  python tmp/diagnostic/probe_new_button.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(r"C:\Users\sarahgamba\Dropbox\PC\Documents\pm-instaprotek")
STORAGE = REPO / ".claude" / "skills" / "instaprotek-enterprise-registration" / ".auth" / "storage_state.json"
OUT = REPO / "tmp" / "diagnostic"
OUT.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://qa.crm.instaprotek.com"


def shot(page, name: str) -> None:
    p = OUT / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        print(f"  [shot] {p}")
    except Exception as e:
        print(f"  [shot-fail] {name}: {e}")


def dump_dialog_buttons(page, label: str) -> None:
    info = page.evaluate(
        """() => {
          const out = {dialogs: []};
          const dlgs = Array.from(document.querySelectorAll('.advancedFullDialog'));
          out.dialog_count = dlgs.length;
          for (const d of dlgs) {
            const rect = d.getBoundingClientRect();
            const dlgInfo = {
              classes: d.className,
              visible: rect.width > 0 && rect.height > 0,
              rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height},
              buttons: [],
            };
            const btns = Array.from(d.querySelectorAll('button'));
            for (const b of btns) {
              const r = b.getBoundingClientRect();
              dlgInfo.buttons.push({
                text: (b.textContent || '').trim().slice(0, 80),
                aria_label: b.getAttribute('aria-label'),
                title: b.getAttribute('title'),
                disabled: b.disabled,
                visible: r.width > 0 && r.height > 0,
                rect: {x: r.x, y: r.y, w: r.width, h: r.height},
                classes: b.className,
                inner_icons: Array.from(b.querySelectorAll('i, .material-icons, [class*=icon]')).map(i => ({
                  tag: i.tagName,
                  cls: i.className,
                  text: (i.textContent || '').trim().slice(0, 40),
                })),
              });
            }
            out.dialogs.push(dlgInfo);
          }
          // any open MUI/react-modal portals?
          out.body_modals = Array.from(document.querySelectorAll('[role=dialog], .modal, .MuiDialog-root, .ReactModal__Content, .advancedFullDialog')).map(m => ({
            cls: m.className,
            role: m.getAttribute('role'),
            visible: m.getBoundingClientRect().width > 0,
            text_preview: (m.textContent || '').trim().slice(0, 120),
          }));
          return out;
        }"""
    )
    print(f"\n=== {label} ===")
    print(f"advancedFullDialog count: {info['dialog_count']}")
    for i, d in enumerate(info["dialogs"]):
        print(f" dialog[{i}] visible={d['visible']} rect={d['rect']}")
        for b in d["buttons"]:
            if not b["visible"]:
                continue
            print(
                f"   btn text={b['text']!r} aria={b['aria_label']!r} "
                f"disabled={b['disabled']} cls={b['classes'][:60]!r} "
                f"icons={[i['text'] for i in b['inner_icons']]}"
            )
    print(f" body modal-like elements: {len(info['body_modals'])}")
    for m in info["body_modals"]:
        if m["visible"]:
            print(f"   modal cls={m['cls'][:60]!r} role={m['role']!r} preview={m['text_preview']!r}")
    # also dump to JSON for offline review
    (OUT / f"{label}.json").write_text(json.dumps(info, indent=2))


def find_plus_new_button(page):
    """Return the green '+ New' button via DOM scan, scoped to Batches tab content."""
    handle = page.evaluate_handle(
        """() => {
          const dlg = document.querySelector('.advancedFullDialog');
          if (!dlg) return null;
          const btns = Array.from(dlg.querySelectorAll('button'));
          // Find buttons whose textContent contains 'New' but not 'Transaction'
          const candidates = btns.filter(b => {
            const t = (b.textContent || '').trim();
            return /\\bNew\\b/.test(t) && !t.includes('Transaction') && !b.disabled;
          });
          return candidates[0] || null;
        }"""
    )
    return handle


def main() -> None:
    if not STORAGE.exists():
        raise SystemExit(f"Storage state missing: {STORAGE}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context(storage_state=str(STORAGE), viewport={"width": 1400, "height": 900})
        page = ctx.new_page()

        # Capture pageerror only (console is noisy)
        page.on("pageerror", lambda e: print(f"[pageerror] {e}"))

        print(f"Navigating to {BASE_URL}/portal/company ...")
        page.goto(f"{BASE_URL}/portal/company", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(1500)
        shot(page, "01_company_landing")

        # Search Demo Company, click it
        try:
            page.get_by_role("textbox", name="Search Companies...").fill("Demo Company", timeout=10000)
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"Company search fill failed: {e}")
        page.get_by_role("cell", name="Demo Company").first.click(timeout=15000)
        page.wait_for_timeout(1500)
        shot(page, "02_company_opened")

        # Plans tab
        page.get_by_role("tab", name="i Plans").click()
        page.wait_for_timeout(800)
        shot(page, "03_plans_tab")

        # Click the plan row by cell text
        page.get_by_role("cell", name="Extended Service Contract - 12 Months").first.click()
        page.wait_for_timeout(1200)
        shot(page, "04_plan_detail_opened")

        dump_dialog_buttons(page, "05_before_batches_tab")

        # Switch to Batches tab
        page.get_by_role("tab", name="s Batches").click()
        page.wait_for_timeout(1500)
        shot(page, "06_batches_tab_active")

        dump_dialog_buttons(page, "07_batches_tab_active")

        # Probe what `get_by_role('button', name='add New')` actually resolves to
        print("\n--- Probing get_by_role('button', name='add New') ---")
        try:
            dlg = page.locator(".advancedFullDialog").first
            scoped = dlg.get_by_role("button", name="add New")
            count = scoped.count()
            print(f"  scoped count = {count}")
            for i in range(count):
                el = scoped.nth(i)
                try:
                    box = el.bounding_box()
                    visible = el.is_visible()
                    text = el.inner_text()
                    print(f"  [{i}] visible={visible} text={text!r} box={box}")
                except Exception as e:
                    print(f"  [{i}] probe failed: {e}")
        except Exception as e:
            print(f"  scoped query failed: {e}")

        # Try alternative names
        for alt in ["+ New", "New", "add_circle New", " New", "add New"]:
            try:
                c = page.locator(".advancedFullDialog").first.get_by_role("button", name=alt).count()
                print(f"  alt name={alt!r} count={c}")
            except Exception as e:
                print(f"  alt name={alt!r} ERROR {e}")

        # Try by text
        try:
            cnt = page.locator(".advancedFullDialog button:has-text('New')").count()
            print(f"  button:has-text('New') count = {cnt}")
        except Exception as e:
            print(f"  has-text probe failed: {e}")

        # ====== ATTEMPT 1: current selector behaviour ======
        print("\n--- ATTEMPT 1: current selector dialog_scope.get_by_role('button', name='add New').first.click() ---")
        try:
            page.locator(".advancedFullDialog").first.get_by_role("button", name="add New").first.click(timeout=5000)
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"  click raised: {e}")
        shot(page, "08_after_current_click")
        dump_dialog_buttons(page, "09_after_current_click")

        # If a dialog/listbox appeared, log it
        try:
            lb = page.get_by_role("listbox", name="Product *").count()
            print(f"  listbox 'Product *' count after current click: {lb}")
        except Exception as e:
            print(f"  listbox probe failed: {e}")

        # ====== ATTEMPT 2: DOM-scoped click on the visible '+ New' button ======
        print("\n--- ATTEMPT 2: native DOM click on first button containing 'New' (not Transaction) inside .advancedFullDialog ---")
        try:
            handle = find_plus_new_button(page)
            if handle:
                page.evaluate("(el) => { el.scrollIntoView(); el.click(); }", handle)
                page.wait_for_timeout(1500)
                shot(page, "10_after_native_click")
                dump_dialog_buttons(page, "11_after_native_click")
                lb2 = page.get_by_role("listbox", name="Product *").count()
                print(f"  listbox 'Product *' count after native click: {lb2}")
            else:
                print("  no candidate found")
        except Exception as e:
            print(f"  native click failed: {e}")

        # ====== ATTEMPT 3: Playwright .click() on the same handle via locator selector ======
        print("\n--- ATTEMPT 3: locator '.advancedFullDialog .greenButton, .advancedFullDialog button.btn-success' click ---")
        for css in [
            ".advancedFullDialog button.greenButton",
            ".advancedFullDialog button.btn-success",
            ".advancedFullDialog .greenButton",
            ".advancedFullDialog button:has-text('New')",
        ]:
            try:
                c = page.locator(css).count()
                print(f"  css={css!r} count={c}")
            except Exception as e:
                print(f"  css={css!r} ERROR {e}")

        print("\nDone. Sleeping 5s so you can inspect, then closing.")
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
