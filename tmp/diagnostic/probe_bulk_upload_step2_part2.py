"""Part 2: open the Company dropdown, dump the menu options structure, choose
'Demo Company', and inspect the Product SKU control that should then appear.

Findings from probe part 1:
- Step 2 dialog is `.bulkDialog`. It uses react-md `md-select-field` (NOT react-select v1).
- Only one [role="listbox"] is in the dialog: id="company-toggle" with the
  Company label. The hidden form input is `<input type="hidden" id="company">`.
- The Product SKU label/control wasn't visible — it must render after a company
  is selected. We need to verify this and capture its selectors.
"""
from __future__ import annotations

import json
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


def shot(page, name: str) -> None:
    p = OUT / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        print(f"  [shot] {p}")
    except Exception as e:
        print(f"  [shot-fail] {name}: {e}")


def dump_dialog(page, label: str) -> dict:
    state = page.evaluate(
        r"""() => {
          const dlg = Array.from(document.querySelectorAll('.bulkDialog'))
            .find(d => d.getBoundingClientRect().width > 0);
          if (!dlg) return {found: false};
          const out = {
            found: true,
            labels: Array.from(dlg.querySelectorAll('label')).map(l => ({
              text: (l.textContent || '').trim(),
              for: l.getAttribute('for'),
              classes: l.className,
            })),
            select_fields: Array.from(dlg.querySelectorAll('.md-select-field')).map(s => {
              const hiddenInput = s.querySelector('input[type="hidden"]');
              const toggle = s.querySelector('[role="listbox"], [role="combobox"]');
              const displayed = s.querySelector('.md-select-field__value, .md-select-field--btn, .md-select-field__label');
              return {
                classes: s.className,
                outer_preview: s.outerHTML.slice(0, 600),
                hidden_input_id: hiddenInput ? hiddenInput.id : null,
                hidden_input_name: hiddenInput ? hiddenInput.name : null,
                hidden_input_value: hiddenInput ? hiddenInput.value : null,
                toggle_id: toggle ? toggle.id : null,
                toggle_role: toggle ? toggle.getAttribute('role') : null,
                toggle_aria_labelledby: toggle ? toggle.getAttribute('aria-labelledby') : null,
                toggle_aria_label: toggle ? toggle.getAttribute('aria-label') : null,
                displayed_text: displayed ? (displayed.textContent || '').trim() : null,
              };
            }),
            listboxes: Array.from(dlg.querySelectorAll('[role="listbox"]')).map(lb => ({
              id: lb.id,
              classes: lb.className,
              aria_label: lb.getAttribute('aria-label'),
              aria_labelledby: lb.getAttribute('aria-labelledby'),
              text: (lb.textContent || '').trim().slice(0, 120),
            })),
            comboboxes: Array.from(dlg.querySelectorAll('[role="combobox"]')).map(c => ({
              id: c.id,
              classes: c.className,
              aria_label: c.getAttribute('aria-label'),
              aria_labelledby: c.getAttribute('aria-labelledby'),
            })),
          };
          // Document-wide menu state (the menu can render in a portal outside the dialog)
          out.global_menus = Array.from(document.querySelectorAll('.md-list--menu, [role="menu"], .md-list--menu-restricted, .md-menu, .md-select-field__menu'))
            .filter(m => m.getBoundingClientRect().width > 0)
            .map(m => ({
              tag: m.tagName,
              classes: m.className,
              text_preview: (m.textContent || '').trim().slice(0, 200),
              outer_preview: m.outerHTML.slice(0, 1500),
            }));
          out.global_listitems = Array.from(document.querySelectorAll('[role="option"]'))
            .filter(o => o.getBoundingClientRect().width > 0)
            .slice(0, 15)
            .map(o => ({
              id: o.id,
              text: (o.textContent || '').trim(),
              classes: o.className,
              aria_selected: o.getAttribute('aria-selected'),
            }));
          return out;
        }"""
    )
    path = OUT / f"{label}.json"
    path.write_text(json.dumps(state, indent=2))
    print(f"  [json] {path}")
    return state


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
            page.wait_for_timeout(1200)
            page.get_by_role("button", name="chevron_right Next").first.click()
            page.wait_for_timeout(2000)
            shot(page, "p2_step2_landed")

            print("\n>> initial Step 2 dump")
            dump_dialog(page, "p2_step2_initial")

            print("\n>> OPENING Company md-select-field (#company-toggle)")
            # Click the toggle by id — this is scoped & unambiguous
            toggle = page.locator("#company-toggle")
            print(f"  toggle count: {toggle.count()}")
            toggle.first.click()
            page.wait_for_timeout(1200)
            shot(page, "p2_company_open")

            print("\n>> dump after company menu opens")
            opened = dump_dialog(page, "p2_step2_company_open")
            print(f"\n  global_menus: {len(opened.get('global_menus', []))}")
            for m in opened.get("global_menus", []):
                print(f"    menu class={m['classes'][:100]!r}")
                print(f"      preview={m['text_preview']!r}")
            print(f"\n  global_listitems (role=option) shown: {len(opened.get('global_listitems', []))}")
            for o in opened.get("global_listitems", []):
                print(f"    option id={o['id']!r} text={o['text']!r} aria_selected={o['aria_selected']}")

            # Try to find a 'Demo Company' option and click it
            print("\n>> trying to click Demo Company option")
            try:
                opt = page.get_by_role("option", name="Demo Company")
                print(f"  get_by_role('option', name='Demo Company') count: {opt.count()}")
                if opt.count() > 0:
                    opt.first.click()
                else:
                    # Fall back: filter by text within the visible menu
                    page.locator("li:has-text('Demo Company'), [role='option']:has-text('Demo Company')").first.click()
            except Exception as e:
                print(f"  ! could not click Demo Company: {e}")
                # Fall back to first option
                page.get_by_role("option").first.click()
            page.wait_for_timeout(1500)
            shot(page, "p2_company_chosen")

            print("\n>> dump after company is chosen — does the SKU field render?")
            after = dump_dialog(page, "p2_step2_company_chosen")
            print(f"\n  labels found:")
            for l in after.get("labels", []):
                if l["text"]:
                    print(f"    {l}")
            print(f"\n  md-select-field count: {len(after.get('select_fields', []))}")
            for s in after.get("select_fields", []):
                print(f"    hidden_id={s['hidden_input_id']!r} hidden_value={s['hidden_input_value']!r}")
                print(f"      toggle_id={s['toggle_id']!r} toggle_aria_labelledby={s['toggle_aria_labelledby']!r}")
                print(f"      displayed_text={s['displayed_text']!r}")
                print(f"      classes={s['classes']!r}")
            print(f"\n  listboxes in dialog now: {len(after.get('listboxes', []))}")
            for lb in after.get("listboxes", []):
                print(f"    {lb}")

            # If a second md-select-field exists, open it and dump menu options
            select_fields = after.get("select_fields", [])
            sku_field = None
            for s in select_fields:
                hid = s.get("hidden_input_id")
                if hid and hid != "company":
                    sku_field = s
                    break
            if sku_field:
                print(f"\n>> OPENING SKU field (hidden id={sku_field['hidden_input_id']!r}, toggle id={sku_field['toggle_id']!r})")
                tid = sku_field["toggle_id"]
                if tid:
                    page.locator(f"#{tid}").first.click()
                else:
                    # fall back to clicking via hidden input wrapper
                    page.locator(f".md-select-field:has(#{sku_field['hidden_input_id']})").first.click()
                page.wait_for_timeout(1200)
                shot(page, "p2_sku_open")
                sku_state = dump_dialog(page, "p2_step2_sku_open")
                print(f"\n  options visible in document after SKU open:")
                for o in sku_state.get("global_listitems", []):
                    print(f"    option id={o['id']!r} text={o['text']!r}")
                # Close menu
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
            else:
                print("\n  ** no second md-select-field detected — SKU field may need a different trigger **")

            # Final: show full role=listbox map after company selection
            lb_count = page.get_by_role("listbox").count()
            print(f"\n>> page-wide listbox count after company selected: {lb_count}")
            for i in range(min(lb_count, 6)):
                lb = page.get_by_role("listbox").nth(i)
                info = lb.evaluate(
                    r"""(el) => ({id: el.id, classes: el.className, text: (el.textContent || '').trim().slice(0, 120), in_dialog: !!el.closest('.bulkDialog')})"""
                )
                print(f"    [{i}] {info}")

            print("\n>> done")
        except Exception:
            print("!! failed:", traceback.format_exc())
            shot(page, "p2_FAILURE")
            return 1
        finally:
            time.sleep(1)
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
