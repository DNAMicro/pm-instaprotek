"""Follow-up probe: open New Batch dialog and dump its full structure.

We've confirmed the dialog DOES open. The 'add New' click is fine. The script
then fails on get_by_role('listbox', name='Product *'), which suggests the
Product field has been re-rendered as something other than a listbox.
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


def shot(page, name: str) -> None:
    p = OUT / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        print(f"  [shot] {p}")
    except Exception as e:
        print(f"  [shot-fail] {name}: {e}")


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context(storage_state=str(STORAGE), viewport={"width": 1400, "height": 900})
        page = ctx.new_page()

        page.goto("https://qa.crm.instaprotek.com/portal/company", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=30000)
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

        # Click the +New button via the existing selector
        page.locator(".advancedFullDialog").first.get_by_role("button", name="add New").first.click()
        page.wait_for_timeout(2000)
        shot(page, "20_new_batch_dialog_open")

        # The dialog is the second .md-dialog (md-dialog--centered) — distinct from advancedFullDialog
        struct = page.evaluate(
            r"""() => {
              // Find the centered dialog opened on top of the advancedFullDialog
              const centered = Array.from(document.querySelectorAll('.md-dialog--centered'))
                .find(d => d.getBoundingClientRect().width > 0);
              if (!centered) return {found: false};
              const out = {
                found: true,
                classes: centered.className,
                inner_html_preview: centered.innerHTML.slice(0, 4000),
                role_elements: {},
                labels: [],
                inputs: [],
                buttons: [],
              };
              ['listbox','combobox','dialog','textbox','option','menu','menuitem','button'].forEach(r => {
                const els = Array.from(centered.querySelectorAll(`[role="${r}"]`));
                out.role_elements[r] = els.map(e => ({
                  aria_label: e.getAttribute('aria-label'),
                  aria_labelledby: e.getAttribute('aria-labelledby'),
                  text: (e.textContent || '').trim().slice(0,80),
                  tag: e.tagName,
                  classes: e.className.slice(0,80),
                }));
              });
              out.labels = Array.from(centered.querySelectorAll('label')).map(l => ({
                text: (l.textContent || '').trim(),
                forAttr: l.getAttribute('for'),
                classes: l.className.slice(0,80),
              }));
              out.inputs = Array.from(centered.querySelectorAll('input')).map(i => ({
                type: i.type,
                name: i.name,
                id: i.id,
                placeholder: i.placeholder,
                value: i.value,
                aria_label: i.getAttribute('aria-label'),
                readonly: i.readOnly,
                disabled: i.disabled,
                classes: i.className.slice(0,80),
              }));
              out.buttons = Array.from(centered.querySelectorAll('button')).map(b => ({
                text: (b.textContent || '').trim().slice(0,80),
                disabled: b.disabled,
                classes: b.className.slice(0,80),
              }));
              return out;
            }"""
        )

        (OUT / "20_new_batch_dialog_struct.json").write_text(json.dumps(struct, indent=2))
        print("\n=== New Batch dialog structure ===")
        print(f"found: {struct.get('found')}")
        print(f"classes: {struct.get('classes')}")
        print("\n-- LABELS --")
        for lab in struct["labels"]:
            print(f"  {lab}")
        print("\n-- INPUTS --")
        for inp in struct["inputs"]:
            print(f"  {inp}")
        print("\n-- ROLE elements --")
        for r, els in struct["role_elements"].items():
            if els:
                print(f"  role={r} count={len(els)}")
                for e in els:
                    print(f"     {e}")
        print("\n-- BUTTONS --")
        for b in struct["buttons"]:
            print(f"  {b}")

        # Specifically probe the Product field area
        print("\n=== Searching for 'Product' label and the control it labels ===")
        prod = page.evaluate(
            r"""() => {
              const centered = Array.from(document.querySelectorAll('.md-dialog--centered'))
                .find(d => d.getBoundingClientRect().width > 0);
              if (!centered) return null;
              // Find label with text 'Product'
              const labels = Array.from(centered.querySelectorAll('label, .md-floating-label, .md-text-field-message, span'))
                .filter(l => /^Product\s*\*?$/.test((l.textContent || '').trim()));
              const result = {label_count: labels.length, labels: []};
              for (const lbl of labels) {
                const info = {
                  text: lbl.textContent.trim(),
                  tag: lbl.tagName,
                  classes: lbl.className,
                  for: lbl.getAttribute('for'),
                  parent_classes: lbl.parentElement ? lbl.parentElement.className : null,
                  grandparent_classes: lbl.parentElement && lbl.parentElement.parentElement ? lbl.parentElement.parentElement.className : null,
                  sibling_html: lbl.parentElement ? lbl.parentElement.outerHTML.slice(0, 1200) : null,
                };
                result.labels.push(info);
              }
              return result;
            }"""
        )
        print(json.dumps(prod, indent=2))

        # Also probe what get_by_role('listbox') matches anywhere on the page
        listbox_count = page.get_by_role("listbox").count()
        print(f"\nGlobal listbox role count: {listbox_count}")
        for i in range(min(listbox_count, 10)):
            lb = page.get_by_role("listbox").nth(i)
            try:
                txt = lb.inner_text()[:80]
                vis = lb.is_visible()
                print(f"  listbox[{i}] visible={vis} text={txt!r}")
            except Exception as e:
                print(f"  listbox[{i}] err {e}")

        combobox_count = page.get_by_role("combobox").count()
        print(f"\nGlobal combobox role count: {combobox_count}")
        for i in range(min(combobox_count, 10)):
            lb = page.get_by_role("combobox").nth(i)
            try:
                txt = lb.inner_text()[:80]
                vis = lb.is_visible()
                aria = lb.evaluate("(el)=>({aria_label: el.getAttribute('aria-label'), aria_labelledby: el.getAttribute('aria-labelledby'), id: el.id})")
                print(f"  combobox[{i}] visible={vis} text={txt!r} attrs={aria}")
            except Exception as e:
                print(f"  combobox[{i}] err {e}")

        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
