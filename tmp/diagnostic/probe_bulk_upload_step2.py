"""Probe the Bulk Upload Step 2 dialog (Company + Product SKU dropdowns).

Goal: confirm the Step 2 fields are react-select v1 (same as the New Batch dialog
that we already fixed), and capture the precise input IDs / .Select-control
selectors that should replace the too-generic `{"role": "listbox"}` entries in
selectors.json.

Strategy:
- Reuse storage_state.json to skip login.
- Navigate to /portal/registration, click Import CSV.
- Step 1: upload `sample_bulk.xlsx` (the validated XLSX copied from
  processed/failures). Click Next.
- Step 2: dump the .bulkDialog DOM — inputs, comboboxes/listboxes, .Select-*
  wrappers, labels, accessible names — to JSON. Take a screenshot.
- Probe the Company and Product SKU `.Select-control` wrappers and report
  the underlying `<input>` id and a candidate `.bulkDialog .Select-control:has(#<id>)`
  selector.
- Close without submitting.
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
OUT.mkdir(parents=True, exist_ok=True)

SAMPLE_XLSX = OUT / "sample_bulk.xlsx"
BASE = "https://qa.crm.instaprotek.com"
HEADLESS = True  # autonomous run; flip to False for visual debug


def shot(page, name: str) -> None:
    p = OUT / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        print(f"  [shot] {p}")
    except Exception as e:
        print(f"  [shot-fail] {name}: {e}")


def dump_dialog_state(page, label: str) -> dict:
    """Walk `.bulkDialog` (with fallbacks) and capture every interactive node."""
    state = page.evaluate(
        r"""() => {
          // Find the visible bulk-upload dialog. Try by class first, then any visible
          // .md-dialog--centered as a fallback.
          let dlg = Array.from(document.querySelectorAll('.bulkDialog'))
            .find(d => d.getBoundingClientRect().width > 0);
          let strategy = '.bulkDialog';
          if (!dlg) {
            dlg = Array.from(document.querySelectorAll('.md-dialog--centered'))
              .find(d => d.getBoundingClientRect().width > 0);
            strategy = '.md-dialog--centered';
          }
          if (!dlg) {
            dlg = Array.from(document.querySelectorAll('[role="dialog"]'))
              .find(d => d.getBoundingClientRect().width > 0);
            strategy = '[role="dialog"]';
          }
          if (!dlg) return {found: false};

          const out = {
            found: true,
            strategy,
            classes: dlg.className,
            outer_html_preview: dlg.outerHTML.slice(0, 8000),
            labels: [],
            inputs: [],
            buttons: [],
            select_controls: [],
            role_elements: {},
            wizard_active_step: null,
          };

          // Wizard step indicator (most wizard dialogs show "Step X of Y" or active step name)
          const stepEl = dlg.querySelector('.md-stepper--active, .active-step, [aria-current="step"]');
          if (stepEl) {
            out.wizard_active_step = (stepEl.textContent || '').trim().slice(0, 120);
          }

          out.labels = Array.from(dlg.querySelectorAll('label, .md-floating-label, .md-text-field-message')).map(l => ({
            text: (l.textContent || '').trim().slice(0, 120),
            tag: l.tagName,
            for: l.getAttribute('for'),
            classes: l.className.slice(0, 120),
          }));

          out.inputs = Array.from(dlg.querySelectorAll('input, select, textarea')).map(i => ({
            tag: i.tagName,
            type: i.type || null,
            name: i.name || null,
            id: i.id || null,
            role: i.getAttribute('role'),
            placeholder: i.placeholder || null,
            value: i.value || null,
            aria_label: i.getAttribute('aria-label'),
            aria_labelledby: i.getAttribute('aria-labelledby'),
            aria_describedby: i.getAttribute('aria-describedby'),
            readonly: i.readOnly,
            disabled: i.disabled,
            classes: i.className.slice(0, 200),
            parent_classes: i.parentElement ? i.parentElement.className.slice(0, 200) : null,
            grandparent_classes: i.parentElement && i.parentElement.parentElement ? i.parentElement.parentElement.className.slice(0, 200) : null,
          }));

          out.buttons = Array.from(dlg.querySelectorAll('button')).map(b => ({
            text: (b.textContent || '').trim().slice(0, 120),
            disabled: b.disabled,
            id: b.id || null,
            classes: b.className.slice(0, 200),
          }));

          // Specifically capture every .Select-control (react-select v1 markers)
          out.select_controls = Array.from(dlg.querySelectorAll('.Select, .Select-control')).map(s => {
            const input = s.querySelector('input');
            const value = s.querySelector('.Select-value, .Select-placeholder');
            return {
              tag: s.tagName,
              classes: s.className.slice(0, 200),
              parent_classes: s.parentElement ? s.parentElement.className.slice(0, 200) : null,
              input_id: input ? input.id : null,
              input_name: input ? input.name : null,
              input_aria_label: input ? input.getAttribute('aria-label') : null,
              input_aria_labelledby: input ? input.getAttribute('aria-labelledby') : null,
              value_text: value ? (value.textContent || '').trim().slice(0, 120) : null,
              outer_html_preview: s.outerHTML.slice(0, 1200),
            };
          });

          // Roles
          ['listbox','combobox','option','menu','menuitem','button','textbox','tab','dialog'].forEach(r => {
            const els = Array.from(dlg.querySelectorAll(`[role="${r}"]`));
            out.role_elements[r] = els.map(e => ({
              tag: e.tagName,
              id: e.id || null,
              aria_label: e.getAttribute('aria-label'),
              aria_labelledby: e.getAttribute('aria-labelledby'),
              text: (e.textContent || '').trim().slice(0, 120),
              classes: e.className.slice(0, 200),
              parent_classes: e.parentElement ? e.parentElement.className.slice(0, 200) : null,
            }));
          });

          // Also count GLOBAL role=listbox (outside the dialog) so we can prove which
          // one the current selector resolves to via .first
          const allListbox = Array.from(document.querySelectorAll('[role="listbox"]'));
          out.global_listbox_count = allListbox.length;
          out.global_listbox_first = allListbox[0] ? {
            id: allListbox[0].id,
            classes: allListbox[0].className.slice(0, 200),
            text: (allListbox[0].textContent || '').trim().slice(0, 120),
            inside_dialog: dlg.contains(allListbox[0]),
          } : null;

          return out;
        }"""
    )

    path = OUT / f"{label}.json"
    path.write_text(json.dumps(state, indent=2))
    print(f"  [json] {path}  (found={state.get('found')} strategy={state.get('strategy')})")
    return state


def main() -> int:
    if not STORAGE.exists():
        print(f"!! storage_state.json missing at {STORAGE}", file=sys.stderr)
        return 2
    if not SAMPLE_XLSX.exists():
        print(f"!! sample XLSX missing at {SAMPLE_XLSX}", file=sys.stderr)
        return 2

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS)
        ctx = browser.new_context(
            storage_state=str(STORAGE),
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.new_page()

        try:
            print(">> navigating to /portal/registration")
            page.goto(BASE + "/portal/registration", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            shot(page, "step0_registrations_landing")

            print(">> clicking Import CSV")
            page.get_by_role("button", name="file_upload Import CSV").first.click()
            page.wait_for_timeout(1500)
            shot(page, "step1_dialog_open")

            # Dump dialog before file selection
            print(">> dumping dialog state BEFORE file selection")
            dump_dialog_state(page, "step1_dialog_state")

            print(">> uploading sample XLSX via file input")
            file_inputs = page.locator("input[type='file']")
            print(f"  file_input count: {file_inputs.count()}")
            file_inputs.first.set_input_files(str(SAMPLE_XLSX))
            page.wait_for_timeout(1500)
            shot(page, "step1_after_file")

            print(">> clicking Next to advance to Step 2")
            try:
                page.get_by_role("button", name="chevron_right Next").first.click(timeout=8000)
            except Exception as e:
                print(f"  ! standard Next click failed: {e}")
                # Try a broader Next match
                page.locator("button:has-text('Next')").first.click()
            page.wait_for_timeout(2500)
            shot(page, "step2_landed")

            print(">> dumping Step 2 dialog state (PRIMARY EVIDENCE)")
            state = dump_dialog_state(page, "step2_dialog_state")

            # Print a focused summary so it shows up directly in the agent log
            print("\n=== STEP 2 SUMMARY ===")
            print(f"strategy: {state.get('strategy')}")
            print(f"dialog classes: {state.get('classes')}")
            print(f"wizard step: {state.get('wizard_active_step')}")
            print(f"global listbox count: {state.get('global_listbox_count')} first: {state.get('global_listbox_first')}")

            print("\n-- LABELS --")
            for l in state.get("labels", []):
                if l["text"]:
                    print(f"  {l}")

            print("\n-- INPUTS --")
            for i in state.get("inputs", []):
                print(f"  {i}")

            print("\n-- BUTTONS --")
            for b in state.get("buttons", []):
                print(f"  {b}")

            print("\n-- .Select / .Select-control wrappers --")
            for s in state.get("select_controls", []):
                print(f"  classes={s['classes']!r}")
                print(f"     input_id={s['input_id']!r} input_name={s['input_name']!r}")
                print(f"     aria_label={s['input_aria_label']!r}  labelledby={s['input_aria_labelledby']!r}")
                print(f"     value={s['value_text']!r}")
                print(f"     parent_classes={s['parent_classes']!r}")

            print("\n-- ROLE elements --")
            for r, els in state.get("role_elements", {}).items():
                if not els:
                    continue
                print(f"  role={r} count={len(els)}")
                for e in els:
                    print(f"     id={e['id']!r} aria_label={e['aria_label']!r} text={e['text']!r} classes={e['classes']!r}")

            # Direct sanity check: can we open each .Select-control and read the menu options?
            print("\n=== PROBE: open each .Select-control inside the dialog ===")
            sel_count = page.evaluate(
                r"""() => {
                  const dlg = Array.from(document.querySelectorAll('.bulkDialog, .md-dialog--centered'))
                    .find(d => d.getBoundingClientRect().width > 0);
                  if (!dlg) return 0;
                  return dlg.querySelectorAll('.Select-control').length;
                }"""
            )
            print(f"  .Select-control count inside dialog: {sel_count}")

            # For each, open it and see what options appear
            for idx in range(sel_count):
                print(f"\n  -- opening .Select-control[{idx}] --")
                ctrl_locator = page.locator(".bulkDialog .Select-control, .md-dialog--centered .Select-control").nth(idx)
                try:
                    info = ctrl_locator.evaluate(
                        r"""(el) => {
                          const input = el.querySelector('input');
                          return {
                            input_id: input ? input.id : null,
                            input_name: input ? input.name : null,
                            wrapper_outer: el.outerHTML.slice(0, 600),
                          };
                        }"""
                    )
                    print(f"     before-open: {info}")
                    ctrl_locator.dispatch_event("mousedown")
                    ctrl_locator.click()
                    page.wait_for_selector(".Select-menu-outer .Select-option", timeout=5000)
                    opts = page.locator(".Select-menu-outer .Select-option")
                    n = opts.count()
                    print(f"     options visible: {n}")
                    for k in range(min(n, 8)):
                        t = (opts.nth(k).inner_text() or "").strip()
                        print(f"       [{k}] {t!r}")
                    shot(page, f"step2_select_{idx}_open")
                    # Close menu by pressing Escape so we can probe the next control cleanly
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(400)
                except Exception as e:
                    print(f"     ! could not open .Select-control[{idx}]: {e}")
                    shot(page, f"step2_select_{idx}_fail")

            # Final proof: what does the current too-generic selector hit?
            print("\n=== Current selector reality check ===")
            current = page.get_by_role("listbox").first
            try:
                cur_info = current.evaluate(
                    r"""(el) => ({
                      id: el.id,
                      classes: el.className,
                      text: (el.textContent || '').trim().slice(0, 120),
                      in_bulk_dialog: !!el.closest('.bulkDialog'),
                      in_dialog: !!el.closest('.md-dialog--centered'),
                      bounding: el.getBoundingClientRect().toJSON ? el.getBoundingClientRect() : null,
                    })"""
                )
                print(f"  get_by_role('listbox').first => {cur_info}")
            except Exception as e:
                print(f"  current selector evaluate failed: {e}")

            print("\n>> done. Closing.")
        except Exception:
            print("!! probe failed:", traceback.format_exc())
            shot(page, "FAILURE")
            return 1
        finally:
            time.sleep(1)
            browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
