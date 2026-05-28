"""Playwright Chromium driver for the InstaProtek QA CRM.

Drives Steps 2-4 of the SOP:

- Step 2: Login -> Settings -> Company -> Demo Company -> Plans -> New Batch -> fill -> Save
- Step 3: Registrations -> Import CSV -> upload file
- Step 4: New Transaction -> dates -> select all -> Submit

Also exposes `read_brand_menu` to scrape the Settings -> Brand list once per run (cached
between runs in config/brand_menu_cache.json).

DOM selectors live in config/selectors.json. The first headed run populates these — the
runner refuses to operate on empty selectors and logs which ones are missing so the operator
can capture them.

Every step takes a screenshot. On exception, an extra failure screenshot is captured.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Playwright is imported lazily so the module can be syntax-checked without the dep.


# ---- Data types ----------------------------------------------------------


@dataclass
class BatchInput:
    # product_label: exact accessible name of the dropdown option — use when you know the full
    #   label (e.g. "Extended Service Contract - 12 Months (ESC030012MO00IK)").
    # product_sku_hint: SKU substring to match inside an option label — looked up from the
    #   reference price list by PO rate. Takes effect only when product_label is empty.
    # If both are empty, the first available option is auto-selected.
    product_label: str
    number_of_pins: int
    po_number: str
    plan_purchase_date: str          # "MM/DD/YYYY"
    plan_purchase_price: str         # e.g. "14.43" — PO unit rate; field is required by the CRM
    vertical: str                    # "Education" etc. — see CRM Vertical dropdown options
    invoice_number: str = ""         # optional
    product_sku_hint: str = ""       # SKU from reference lookup; used to narrow the product dropdown


@dataclass
class TransactionInput:
    transaction_date: str            # "MM/DD/YYYY" — usually PO order date
    effective_date: str              # "MM/DD/YYYY" — usually first row's Delivery Date


@dataclass
class BulkUploadInput:
    file_path: Path
    company_name: str                # Company dropdown on Step 2
    product_sku: str                 # Product SKU/Barcode dropdown on Step 2 (e.g. plan SKU)


@dataclass
class RunnerResult:
    success: bool
    stage: str
    details: dict[str, Any] = field(default_factory=dict)
    brand_menu_entries: list[dict[str, str]] | None = None
    error: str | None = None


# ---- Selector helpers ----------------------------------------------------


class SelectorMissing(RuntimeError):
    """Raised when a required selector is empty in selectors.json."""


def _require(selectors: dict[str, Any], dotted: str) -> Any:
    parts = dotted.split(".")
    cursor: Any = selectors
    for p in parts:
        if not isinstance(cursor, dict) or p not in cursor:
            raise SelectorMissing(f"Selector missing in selectors.json: {dotted}")
        cursor = cursor[p]
    if cursor in (None, "", [], {}):
        raise SelectorMissing(f"Selector empty in selectors.json: {dotted}")
    return cursor


def _locator(page, selector_value: Any):
    """Resolve a selector value into a Playwright locator.

    Supports:
      - str  -> page.locator(value)
      - {"role": "button", "name": "Save"} -> page.get_by_role(role, name=name)
      - {"label": "Username"} -> page.get_by_label(label)
      - {"text": "..."} -> page.get_by_text(text, exact=True)
      - {"test_id": "..."} -> page.get_by_test_id(test_id)
      - {"placeholder": "..."} -> page.get_by_placeholder(placeholder)
    """
    if isinstance(selector_value, str):
        return page.locator(selector_value)
    if isinstance(selector_value, dict):
        if "role" in selector_value:
            kwargs = {"name": selector_value["name"]} if "name" in selector_value else {}
            return page.get_by_role(selector_value["role"], **kwargs)
        if "label" in selector_value:
            return page.get_by_label(selector_value["label"])
        if "text" in selector_value:
            return page.get_by_text(selector_value["text"], exact=selector_value.get("exact", True))
        if "test_id" in selector_value:
            return page.get_by_test_id(selector_value["test_id"])
        if "placeholder" in selector_value:
            return page.get_by_placeholder(selector_value["placeholder"])
    raise ValueError(f"Unrecognized selector descriptor: {selector_value!r}")


def _safe(value: str) -> str:
    """File-system-safe slug derived from an arbitrary string."""
    out = "".join(c if c.isalnum() else "_" for c in (value or "").lower())
    return out.strip("_")[:40] or "unknown"


# JS that sets an <input>'s value the way React requires: invoke the prototype's value setter
# (bypasses React's controlled-input fence) and dispatch input + change events so React state
# syncs. Returns the value back as a sanity check.
_REACT_SET_INPUT_JS = """(el, value) => {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.dispatchEvent(new Event('blur', { bubbles: true }));
  return el.value;
}"""


def _react_set_input(page, css_selector: str, value: str) -> None:
    """Set a React-controlled <input>'s value via the prototype setter. Use for fields where
    Playwright's .fill() is rejected (notably the react-datepicker text inputs)."""
    page.locator(css_selector).first.evaluate(_REACT_SET_INPUT_JS, value)


def _react_set_date_by_label(page, label_text: str, value: str) -> str:
    """Find the date input whose nearest label contains `label_text` and set its value via
    the React-aware prototype setter. Returns the input's value after the set (for verification).

    Used because the New Batch dialog has multiple `.react-datepicker-component` inputs
    (Plan Purchase Date AND Expiration Date) and a class-based selector picks the wrong one.
    Approach: find a SMALL element (<80 chars of text) whose own text starts with the desired
    label, then look for a date input in its sibling container or the surrounding field group.
    """
    result = page.evaluate(
        """({labelText, value}) => {
          const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
          const want = norm(labelText);

          const isDateInput = (el) => {
              if (!el || el.tagName !== 'INPUT') return false;
              if (el.type && el.type !== 'text') return false;
              const ph = (el.placeholder || '').toLowerCase();
              const cls = (el.className || '').toLowerCase();
              // mm/dd/yyyy placeholder, or react-datepicker / batch-Datepicker class somewhere up the tree
              if (ph.includes('mm/dd') || ph.includes('yyyy')) return true;
              let p = el.parentElement;
              for (let i = 0; i < 5 && p; i++) {
                  if (p.classList && (
                      p.classList.contains('react-datepicker-component') ||
                      p.classList.contains('batch-Datepicker') ||
                      Array.from(p.classList).some(c => c.toLowerCase().includes('datepicker'))
                  )) return true;
                  p = p.parentElement;
              }
              return false;
          };

          // Strategy 1: find a SMALL element whose own text starts with the label.
          // Then walk up to a parent that also contains a date input.
          let target = null;
          const candidates = Array.from(document.querySelectorAll(
              'label, span, div, .md-floating-label, .md-text-field-message'
          ));
          for (const el of candidates) {
              const t = norm(el.innerText || el.textContent || '');
              if (t.length === 0 || t.length > 80) continue;
              if (!t.startsWith(want)) continue;
              // Search nearby for a date input: check siblings, then walk up
              let scope = el;
              for (let i = 0; i < 6 && scope && !target; i++) {
                  const ins = Array.from(scope.querySelectorAll('input'));
                  for (const inp of ins) {
                      if (isDateInput(inp)) { target = inp; break; }
                  }
                  scope = scope.parentElement;
              }
              if (target) break;
          }

          // Strategy 2 (last-resort): collect all date inputs in the dialog. If exactly 2
          // and label is "Plan Purchase Date", pick the LAST one (Plan Purchase Date is at
          // the bottom of the New Batch dialog, Expiration Date is above).
          if (!target) {
              const dialog = document.querySelector('.md-dialog--centered, .userDialog, [role="dialog"]') || document;
              const dateInputs = Array.from(dialog.querySelectorAll('input')).filter(isDateInput);
              if (dateInputs.length >= 1) {
                  if (want.includes('plan purchase')) target = dateInputs[dateInputs.length - 1];
                  else if (want.includes('expiration')) target = dateInputs[0];
                  else target = dateInputs[0];
              }
          }

          if (!target) return null;
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          setter.call(target, value);
          target.dispatchEvent(new Event('input', { bubbles: true }));
          target.dispatchEvent(new Event('change', { bubbles: true }));
          target.dispatchEvent(new Event('blur', { bubbles: true }));
          return target.value;
        }""",
        {"labelText": label_text, "value": value},
    )
    return result or ""


def _react_close_datepicker(page, css_selector_for_input: str) -> None:
    """react-datepicker-component leaves its calendar open after a JS value-set, and the open
    calendar overlay intercepts pointer events on neighboring buttons (notably Save). Click
    the picker's icon to toggle the calendar closed before continuing.
    """
    page.evaluate(
        """(sel) => {
          const inp = document.querySelector(sel);
          if (!inp) return;
          const dp = inp.closest('.react-datepicker-component');
          if (!dp) return;
          const icon = dp.querySelector('.icon-rc-datepicker, .input-button');
          if (icon) icon.click();
        }""",
        css_selector_for_input,
    )


def _react_close_all_datepickers(page) -> None:
    """Close every open react-datepicker calendar on the page."""
    page.evaluate(
        """() => {
          for (const dp of document.querySelectorAll('.react-datepicker-component')) {
              const icon = dp.querySelector('.icon-rc-datepicker, .input-button');
              const cal = dp.querySelector('.react-datepicker-popper, .react-datepicker');
              if (icon && cal) icon.click();
          }
        }"""
    )


def _js_click_button_by_text(page, text: str) -> bool:
    """Force-click a button whose textContent contains `text`. Last-resort when an overlay
    is intercepting Playwright's pointer events. Returns True if a button was clicked."""
    return bool(page.evaluate(
        """(t) => {
          const btns = Array.from(document.querySelectorAll('button'));
          const target = btns.reverse().find(b => b.textContent && b.textContent.includes(t) && !b.disabled);
          if (!target) return false;
          target.click();
          return true;
        }""",
        text,
    ))


def _shot(page, screenshot_dir: Path, name: str) -> Path:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{datetime.utcnow().strftime('%H%M%S')}_{name}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception:
        pass
    return path


# ---- Runner ---------------------------------------------------------------


class CRMRunner:
    """Wraps a single Playwright browser/context/page lifecycle for one orchestrator run."""

    def __init__(
        self,
        *,
        settings: dict[str, Any],
        selectors: dict[str, Any],
        credentials,
        headless: bool,
        screenshot_dir: Path,
        storage_state_path: Path,
        logger: logging.Logger,
    ) -> None:
        self.settings = settings
        self.selectors = selectors
        self.credentials = credentials
        self.headless = headless
        self.screenshot_dir = screenshot_dir
        self.storage_state_path = storage_state_path
        self.logger = logger
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self) -> "CRMRunner":
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        context_kwargs: dict[str, Any] = {
            "user_agent": self.settings["playwright"].get("user_agent"),
        }
        if self.storage_state_path.exists():
            try:
                context_kwargs["storage_state"] = str(self.storage_state_path)
            except Exception:
                pass
        self._context = self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self.settings["playwright"].get("default_timeout_ms", 30000))
        self._context.set_default_navigation_timeout(self.settings["playwright"].get("navigation_timeout_ms", 45000))
        self._page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._context:
                try:
                    self.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
                    self._context.storage_state(path=str(self.storage_state_path))
                except Exception as e:
                    self.logger.warning("Failed to persist storage state: %s", e)
                self._context.close()
        finally:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()

    # -- public steps ------------------------------------------------------

    def login(self) -> None:
        page = self._page
        base = self.settings["crm"]["base_url"].rstrip("/")
        login_path = self.settings["crm"].get("login_path", "/")
        page.goto(base + login_path, wait_until="domcontentloaded")

        # Let the SPA settle so we can reliably distinguish login form vs. restored session.
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        _shot(page, self.screenshot_dir, "login_loaded")

        username_sel = _require(self.selectors, "login.username_input")
        password_sel = _require(self.selectors, "login.password_input")
        submit_sel = _require(self.selectors, "login.submit_button")
        indicator_sel = _require(self.selectors, "login.post_login_indicator")

        # Race: wait for whichever appears first — the username input (need to log in) or the
        # post-login indicator (storage state restored). Poll with a 10s budget.
        import time as _time
        deadline = _time.monotonic() + 10
        already_logged_in = False
        while _time.monotonic() < deadline:
            try:
                if _locator(page, indicator_sel).first.is_visible(timeout=500):
                    already_logged_in = True
                    break
            except Exception:
                pass
            try:
                if _locator(page, username_sel).first.is_visible(timeout=500):
                    break
            except Exception:
                pass

        if already_logged_in:
            self.logger.info("Already logged in (session restored from storage state).")
            _shot(page, self.screenshot_dir, "login_success")
            return

        _locator(page, username_sel).first.fill(self.credentials.username)
        _locator(page, password_sel).first.fill(self.credentials.password)
        _shot(page, self.screenshot_dir, "login_filled")
        _locator(page, submit_sel).first.click()
        _locator(page, indicator_sel).first.wait_for(state="visible")
        _shot(page, self.screenshot_dir, "login_success")

    def read_brand_list(self) -> list[str]:
        """Navigate Settings -> Brand, paginate through the brand table, return brand names.

        The Brand page is a single-column list (Image | Brand Name | Actions); the Brand
        Name lives in cell index 1 of each data row. The page paginates with the bottom-
        right arrow button inside the table footer's "Rows per page" row.
        """
        page = self._page
        self._navigate_to_brand_list()
        names = self._scrape_paginated_column(col_index=1, kind="brand")
        self.logger.info("Brand list read: %d brands", len(names))
        return names

    def read_devices_for_brand(self, brand_name: str) -> list[str]:
        """Navigate Settings -> Brand -> search <brand> -> edit -> Devices tab; paginate.

        Devices live in cell index 1 of each data row in the Devices table.
        """
        page = self._page
        self._navigate_to_brand_list()
        search_input = _require(self.selectors, "settings.brand_search_input")
        loc = _locator(page, search_input).first
        loc.fill("")
        loc.fill(brand_name)

        # Wait for the async filter to render the target row before scanning (Brand Name lives
        # in cell index 1 of the brand-list table).
        self._wait_for_filtered_row(brand_name, cell_index=1)

        # Click the edit button on the row whose visible text contains the brand name. Multi-
        # word brand names ("Samsung Galaxy") collide with substring matches ("Samsung"), so
        # we additionally check the brand-name cell text equals the requested name before
        # clicking.
        target_norm = (brand_name or "").strip().lower()
        rows = page.get_by_role("row")
        n = rows.count()
        edit_button = None
        for i in range(n):
            row = rows.nth(i)
            # Skip header rows (those use columnheader, not cell)
            cells = row.get_by_role("cell")
            if cells.count() < 2:
                continue
            name_text = (cells.nth(1).inner_text() or "").strip().lower()
            if name_text == target_norm:
                edit_button = row.get_by_role("button", name="edit").first
                break
        if edit_button is None:
            _shot(page, self.screenshot_dir, f"FAILURE_brand_not_found_{_safe(brand_name)}")
            raise RuntimeError(f"Brand {brand_name!r} not found in CRM Brand list")
        edit_button.click()
        # Wait for the Devices tab content
        devices_tab = _require(self.selectors, "brand_detail.devices_tab")
        _locator(page, devices_tab).first.wait_for(state="visible")
        _shot(page, self.screenshot_dir, f"brand_devices_loaded_{_safe(brand_name)}")
        devices = self._scrape_paginated_column(col_index=1, kind="device")
        self.logger.info("Devices read for brand %r: %d", brand_name, len(devices))
        return devices

    # -- internal nav + scraping helpers ----------------------------------

    def _wait_for_filtered_row(
        self,
        target: str,
        *,
        cell_index: int = 0,
        timeout_ms: int = 15000,
    ) -> None:
        """Wait until a table row's cell at `cell_index` equals `target` (case-insensitive).

        CRM tables filter asynchronously: typing into the search input fires a server request
        and the previous page's rows stay visible (with a "Getting Records..." overlay) until
        the response arrives. Callers should fill the search input, then call this before
        iterating rows.
        """
        target_norm = (target or "").strip().lower()
        if not target_norm:
            return
        try:
            self._page.wait_for_function(
                """({target, idx}) => {
                    const loading = Array.from(document.querySelectorAll('*')).some(
                        el => el.children.length === 0
                            && (el.textContent || '').trim() === 'Getting Records...'
                    );
                    if (loading) return false;
                    const rows = document.querySelectorAll('[role="row"]');
                    for (const row of rows) {
                        const cells = row.querySelectorAll('[role="cell"]');
                        if (cells.length > idx) {
                            const text = (cells[idx].textContent || '').trim().toLowerCase();
                            if (text === target) return true;
                        }
                    }
                    return false;
                }""",
                arg={"target": target_norm, "idx": cell_index},
                timeout=timeout_ms,
            )
        except Exception:
            # Caller raises a clean error if the row never appears.
            pass

    def _navigate_to_brand_list(self) -> None:
        """Ensure the page is showing Settings -> Brand. Uses direct URL nav for resilience."""
        page = self._page
        base = self.settings["crm"]["base_url"].rstrip("/")
        target = base + "/portal/brand"
        if not page.url.startswith(target):
            page.goto(target)
        # Wait for the brand-search input as a signal that the table has rendered
        try:
            search_input = _require(self.selectors, "settings.brand_search_input")
            _locator(page, search_input).first.wait_for(state="visible", timeout=15000)
        except Exception:
            pass

    def _scrape_paginated_column(self, *, col_index: int, kind: str) -> list[str]:
        """Iterate through all pages of the currently visible table, returning text of the
        Nth cell (`col_index`, 0-based) for every data row.

        Data rows are identified by having at least one `role=cell` (header rows use
        `columnheader`). Pagination uses the footer arrow button inside the row whose
        accessible name contains "Rows per page".
        """
        page = self._page
        items: list[str] = []
        seen: set[str] = set()
        page_index = 0
        while True:
            page_index += 1
            page.wait_for_timeout(250)  # allow rows to settle after pagination/filter
            rows = page.get_by_role("row")
            count = rows.count()
            added = 0
            for i in range(count):
                row = rows.nth(i)
                try:
                    cells = row.get_by_role("cell")
                    if cells.count() <= col_index:
                        continue
                    text = (cells.nth(col_index).inner_text() or "").strip()
                    if not text:
                        continue
                    # Skip pagination row whose only cell is the "Rows per page: ..." string
                    if "rows per page" in text.lower():
                        continue
                    if text in seen:
                        continue
                    seen.add(text)
                    items.append(text)
                    added += 1
                except Exception as exc:
                    self.logger.debug("Row read failed (kind=%s, i=%d): %s", kind, i, exc)
            self.logger.debug("Scraped %s page %d: +%d (total %d)", kind, page_index, added, len(items))
            # Find footer pagination next button
            try:
                footer_row = page.get_by_role("row").filter(has_text="Rows per page").first
                next_btn = footer_row.get_by_role("button", name="keyboard_arrow_right").first
                if not next_btn.is_visible(timeout=1000):
                    break
                if not next_btn.is_enabled():
                    break
                next_btn.click()
            except Exception:
                # No pagination row, or button vanished — single page
                break
            if page_index > 200:  # belt + suspenders against infinite loops
                self.logger.warning("Pagination loop aborted at page %d", page_index)
                break
        return items

    def open_company_and_plan(self, company_name: str, plan_name: str) -> None:
        """Navigate Settings -> Company -> <company_name> -> Plans tab -> click <plan_name>.

        Uses the Company-list search input + exact-name row-cell match so the company can
        be any tenant (Demo Company for QA, buyer's company name in Production). Hard-fails
        with a clear error if the company or plan can't be located.
        """
        page = self._page
        base = self.settings["crm"]["base_url"].rstrip("/")
        if not page.url.startswith(base + "/portal/company"):
            page.goto(base + "/portal/company")
        search_input = _require(self.selectors, "company.company_search_input")
        loc = _locator(page, search_input).first
        loc.wait_for(state="visible", timeout=15000)
        loc.fill("")
        loc.fill(company_name)

        # Wait for the async filter to render the target row before scanning (Company Name
        # lives in cell index 0 of the company-list table).
        self._wait_for_filtered_row(company_name, cell_index=0)

        # Find the row whose name cell equals `company_name` and click into it.
        target_norm = (company_name or "").strip().lower()
        rows = page.get_by_role("row")
        company_cell = None
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.get_by_role("cell")
            if cells.count() < 1:
                continue
            cell_text = (cells.nth(0).inner_text() or "").strip().lower()
            if cell_text == target_norm:
                company_cell = cells.nth(0)
                break
        if company_cell is None:
            _shot(page, self.screenshot_dir, f"FAILURE_company_not_found_{_safe(company_name)}")
            raise RuntimeError(f"Company {company_name!r} not found in CRM Company list")
        company_cell.click()

        # The click triggers an async navigation to Company Details. Confirm the transition
        # actually completed before touching the Plans tab — the Plans tab does not exist on
        # the Companies list page, so a premature click silently fails.
        try:
            page.get_by_role("heading", name=f"Company: {company_name}").first.wait_for(
                state="visible", timeout=15000
            )
        except Exception:
            self.logger.debug("Company Details heading didn't appear within 15s")
        # Also wait for the Company Details tablist to render — the heading appears before
        # the tab list is interactive when state is restored from prior session.
        try:
            page.locator("ul.md-tabs[role='tablist']").first.wait_for(state="visible", timeout=10000)
            # Give the tablist's icons / aria-selected attribute one render cycle to settle.
            page.wait_for_timeout(800)
        except Exception:
            self.logger.debug("Company Details tablist didn't appear within 10s")
        _shot(page, self.screenshot_dir, f"company_selected_{_safe(company_name)}")

        # Plans tab + plan row. The tab DOM is:
        #   <li role="tab"><i class="md-icon--tab ..."></i><div class="md-tab-label">Plans</div></li>
        # Playwright's .click() resolves coordinates and sometimes routes to an adjacent tab
        # (PRODUCTS) when the Material Design tabs are still settling. Click via native JS to
        # avoid coordinate-based dispatch. Confirm by waiting for content unique to the Plans
        # tab; retry up to 3× if it didn't take.
        plans_search_sel = self.selectors.get("company", {}).get("plans_search_input")

        def _click_plans_tab_js() -> str | None:
            return page.evaluate(
                """() => {
                    const labels = document.querySelectorAll('.md-tab-label');
                    for (const lbl of labels) {
                        if ((lbl.textContent || '').trim() === 'Plans') {
                            const tab = lbl.closest("[role='tab']");
                            if (tab) {
                                tab.click();
                                return tab.id || 'unknown';
                            }
                        }
                    }
                    return null;
                }"""
            )

        clicked_id = None
        for attempt in range(3):
            clicked_id = _click_plans_tab_js()
            self.logger.debug("Plans tab JS click attempt %d -> id=%r", attempt + 1, clicked_id)
            if clicked_id is None:
                page.wait_for_timeout(1000)
                continue
            if plans_search_sel is None:
                page.wait_for_timeout(500)
                break
            # Verify the click took by checking aria-selected on the clicked tab.
            try:
                page.wait_for_function(
                    """(id) => {
                        const el = document.getElementById(id);
                        return el && el.getAttribute('aria-selected') === 'true';
                    }""",
                    arg=clicked_id,
                    timeout=5000,
                )
            except Exception:
                self.logger.debug("Plans tab aria-selected didn't flip on attempt %d", attempt + 1)
                continue
            try:
                _locator(page, plans_search_sel).first.wait_for(state="visible", timeout=5000)
                _shot(page, self.screenshot_dir, "plans_tab_active")
                break
            except Exception:
                self.logger.debug("Plans tab click attempt %d didn't reveal search; retrying", attempt + 1)
        else:
            self.logger.warning("Plans tab didn't switch after 3 attempts; continuing anyway")
            _shot(page, self.screenshot_dir, "plans_tab_switch_failed")

        # The CRM has started auto-swapping Plans → Products tab after a short delay
        # (observed 2026-05-15). The Plans subtree mounts, then detaches mid-interaction.
        # Re-click Plans whenever we detect the subtree is gone, then retry the fill.
        def _plans_tab_is_active() -> bool:
            try:
                return bool(page.evaluate(
                    """() => {
                        const labels = document.querySelectorAll('.md-tab-label');
                        for (const lbl of labels) {
                            if ((lbl.textContent || '').trim() === 'Plans') {
                                const tab = lbl.closest("[role='tab']");
                                return !!(tab && tab.getAttribute('aria-selected') === 'true');
                            }
                        }
                        return false;
                    }"""
                ))
            except Exception:
                return False

        def _re_click_plans_tab() -> bool:
            for attempt in range(3):
                clicked = _click_plans_tab_js()
                self.logger.debug("Plans tab re-click attempt %d -> id=%r", attempt + 1, clicked)
                if clicked is None:
                    page.wait_for_timeout(500)
                    continue
                try:
                    page.wait_for_function(
                        """(id) => {
                            const el = document.getElementById(id);
                            return el && el.getAttribute('aria-selected') === 'true';
                        }""",
                        arg=clicked,
                        timeout=3000,
                    )
                    return True
                except Exception:
                    page.wait_for_timeout(500)
            return False

        plans_search = self.selectors.get("company", {}).get("plans_search_input")
        if plans_search:
            for fill_attempt in range(4):
                try:
                    if not _plans_tab_is_active():
                        self.logger.debug("Plans tab no longer active before fill attempt %d; re-clicking", fill_attempt + 1)
                        _re_click_plans_tab()
                    ploc = _locator(page, plans_search).first
                    ploc.wait_for(state="visible", timeout=5000)
                    ploc.fill("")
                    ploc.fill(plan_name)
                    self._wait_for_filtered_row(plan_name, cell_index=0)
                    break
                except Exception as exc:
                    msg = str(exc)
                    self.logger.debug("Plans search fill/wait attempt %d failed: %s", fill_attempt + 1, msg)
                    # If the Plans subtree detached, the CRM likely flipped to Products. Re-click and retry.
                    if not _re_click_plans_tab():
                        self.logger.debug("Plans tab re-click did not stick on attempt %d", fill_attempt + 1)
                        page.wait_for_timeout(500)

        # Final guard: ensure we're still on Plans before the row scan.
        if not _plans_tab_is_active():
            self.logger.warning("Plans tab not active before row scan; forcing re-click")
            _re_click_plans_tab()
            # Give the table a moment to render after the re-click
            page.wait_for_timeout(1000)

        _shot(page, self.screenshot_dir, "before_plan_row_scan")

        # Click the plan row whose first text cell equals `plan_name`
        target_plan = (plan_name or "").strip().lower()
        rows = page.get_by_role("row")
        plan_cell = None
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.get_by_role("cell")
            if cells.count() < 1:
                continue
            cell_text = (cells.nth(0).inner_text() or "").strip().lower()
            if cell_text == target_plan:
                plan_cell = cells.nth(0)
                break
        if plan_cell is None:
            _shot(page, self.screenshot_dir, f"FAILURE_plan_not_found_{_safe(plan_name)}")
            raise RuntimeError(
                f"Plan {plan_name!r} not found under company {company_name!r}"
            )
        plan_cell.click()
        _shot(page, self.screenshot_dir, f"plan_selected_{_safe(plan_name)}")

    def create_batch(self, batch: BatchInput) -> dict[str, str]:
        """Open the New Batch dialog, fill the form, click Save & Continue.

        Notes captured from the 2026-05-12 first-run end-to-end:
        - Product dropdown usually has exactly one option (the product associated with the
          current Plan). If `batch.product_label` is empty we auto-pick it.
        - Plan Purchase Date is a react-datepicker-component input that rejects Playwright
          `.fill()`. We use the JS prototype-setter and explicitly close the calendar
          afterward — its overlay otherwise intercepts the Save button's pointer events.
        - The Save & Continue button is sometimes still intercepted; we fall back to a
          JS .click() if Playwright's click is blocked.
        """
        page = self._page

        # The Plan Detail modal (`.advancedFullDialog`) opens on its Details tab by default.
        # The visible "add New" button on the outer Company > Plans page (which would add
        # another Plan) is now obscured by this dialog's title, so a global `.first` click is
        # intercepted. Switch to the Batches tab inside the dialog, then click "add New"
        # inside the dialog.
        try:
            page.locator(".advancedFullDialog").first.wait_for(state="visible", timeout=10000)
        except Exception:
            self.logger.debug("advancedFullDialog wrapper not detected; continuing")

        batches_tab_sel = self.selectors.get("plan_detail", {}).get("batches_tab")
        if batches_tab_sel:
            try:
                _locator(page, batches_tab_sel).first.click(timeout=5000)
                page.wait_for_timeout(500)  # let the tab content render
            except Exception:
                self.logger.debug("Batches tab click failed (already active?)")

        try:
            dialog_scope = page.locator(".advancedFullDialog").first
            dialog_scope.get_by_role("button", name="add New").first.click()
        except Exception:
            self.logger.debug("Scoped add-New click failed; falling back to global selector")
            new_batch_btn = _require(self.selectors, "company.new_batch_button")
            _locator(page, new_batch_btn).first.click()
        # Wait for the centered New Batch dialog to actually render before screenshotting / probing.
        try:
            page.wait_for_selector(".md-dialog--centered .userDialog", timeout=10000)
        except Exception:
            self.logger.debug("New Batch dialog (.md-dialog--centered .userDialog) didn't appear in 10s")
        _shot(page, self.screenshot_dir, "new_batch_dialog")

        # Product — react-select v1 control. Open with mousedown (click alone doesn't trigger),
        # then pick from .Select-menu-outer .Select-option. Option text observed:
        # "Extended Service Contract - 12 Months (ESC030012MO00IK)".
        product_dropdown = _require(self.selectors, "batch_form.product_dropdown")
        product_ctrl = _locator(page, product_dropdown).first
        product_ctrl.dispatch_event("mousedown")
        product_ctrl.click()
        page.wait_for_selector(".Select-menu-outer .Select-option", timeout=10000)
        option_list = _locator(page, _require(self.selectors, "batch_form.product_option_list"))
        if batch.product_label:
            chosen_option = option_list.filter(has_text=batch.product_label).first
        elif batch.product_sku_hint:
            chosen_option = None
            for i in range(option_list.count()):
                opt = option_list.nth(i)
                if batch.product_sku_hint in (opt.inner_text() or ""):
                    chosen_option = opt
                    break
            if chosen_option is None:
                self.logger.warning(
                    "SKU hint %r not found in Product dropdown; falling back to first option",
                    batch.product_sku_hint,
                )
                chosen_option = option_list.first
        else:
            chosen_option = option_list.first
        chosen_product_label = (chosen_option.inner_text() or "").strip()
        chosen_option.click()

        _locator(page, _require(self.selectors, "batch_form.number_of_pins_input")).first.fill(
            str(batch.number_of_pins)
        )
        _locator(page, _require(self.selectors, "batch_form.po_number_input")).first.fill(
            batch.po_number
        )
        if batch.invoice_number:
            _locator(page, _require(self.selectors, "batch_form.invoice_number_input")).first.fill(
                batch.invoice_number
            )
        _locator(page, _require(self.selectors, "batch_form.plan_purchase_price_input")).first.fill(
            batch.plan_purchase_price
        )

        # Plan Purchase Date — react-datepicker. Use label-based targeting because the
        # dialog now has multiple .react-datepicker-component inputs (Plan Purchase Date
        # and Expiration Date) and the old class-based selector picks the wrong one.
        actual_date = _react_set_date_by_label(page, "Plan Purchase Date", batch.plan_purchase_date)
        if not actual_date or actual_date != batch.plan_purchase_date:
            self.logger.warning(
                "Plan Purchase Date set to %r but field reports %r — date may not have stuck",
                batch.plan_purchase_date, actual_date,
            )
        else:
            self.logger.info("Plan Purchase Date set to %r (verified)", actual_date)
        _react_close_all_datepickers(page)

        # Vertical — same react-select v1 pattern as Product.
        vertical_ctrl = _locator(page, _require(self.selectors, "batch_form.vertical_dropdown")).first
        vertical_ctrl.dispatch_event("mousedown")
        vertical_ctrl.click()
        page.wait_for_selector(".Select-menu-outer .Select-option", timeout=10000)
        _locator(page, _require(self.selectors, "batch_form.vertical_option_list")).filter(
            has_text=batch.vertical
        ).first.click()

        _shot(page, self.screenshot_dir, "batch_filled")

        # Save & Continue — try Playwright click first, fall back to JS click if overlay intercepts
        save_btn = _locator(page, _require(self.selectors, "batch_form.save_and_continue_button")).first
        try:
            save_btn.click(timeout=5000)
        except Exception:
            self.logger.info("Save & Continue intercepted; falling back to JS click")
            if not _js_click_button_by_text(page, "Save & Continue"):
                raise
        # Wait until the batch detail page loads
        page.wait_for_url("**/portal/company/**", timeout=30_000)
        _shot(page, self.screenshot_dir, "batch_saved")
        # Capture the batch detail URL so Step 4 can navigate back directly instead of
        # searching the Batches table (which is racy and may not even show a PO Number column).
        self._last_batch_url = page.url
        self.logger.info("Batch detail URL captured: %s", self._last_batch_url)

        # Pull the product SKU out of the option label (last "(...)" group)
        import re as _re
        sku_match = _re.search(r"\(([^()]+)\)\s*$", chosen_product_label)
        product_sku = sku_match.group(1) if sku_match else ""
        return {"product_label": chosen_product_label, "product_sku": product_sku, "batch_url": self._last_batch_url}

    def import_csv(self, upload: BulkUploadInput) -> None:
        """Drive the global Registrations -> Import CSV 3-step Bulk Upload dialog.

        Captured 2026-05-12: registrations are uploaded at /portal/registration (NOT within
        a plan/batch). Step 2 asks for Company and Product SKU (the plan SKU / barcode).
        Step 3 shows "File Imported Successfully" on success.
        """
        page = self._page
        base = self.settings["crm"]["base_url"].rstrip("/")
        if not page.url.startswith(base + "/portal/registration"):
            page.goto(base + "/portal/registration")

        _locator(page, _require(self.selectors, "registrations.import_csv_button")).first.click()
        _shot(page, self.screenshot_dir, "bulk_upload_step1")

        # Step 1: file
        file_input_css = _require(self.selectors, "registrations.file_input")
        page.locator(file_input_css).first.set_input_files(str(upload.file_path))
        _shot(page, self.screenshot_dir, "bulk_upload_file_selected")

        # Advance to Step 2
        _locator(page, _require(self.selectors, "registrations.step1_next_button")).first.click()

        # Step 2: Company + Product SKU.
        # These are react-md md-select-field controls (NOT react-select v1). The toggles
        # are stable ids #company-toggle / #register_under-toggle inside .bulkDialog.
        # The SKU toggle is NOT in the DOM until a Company is selected. Menu items render
        # in a document-level portal as [role=option] — match by accessible name.
        page.wait_for_selector(".bulkDialog #company-toggle", timeout=10000)
        _locator(page, _require(self.selectors, "registrations.step2_company_dropdown")).first.click()
        page.wait_for_selector("[role='option']", timeout=10000)
        page.get_by_role("option", name=upload.company_name, exact=True).first.click()

        sku_wait = self.selectors.get("registrations", {}).get(
            "step2_company_dropdown_wait", ".bulkDialog #register_under-toggle"
        )
        page.wait_for_selector(sku_wait, timeout=10000)
        _locator(page, _require(self.selectors, "registrations.step2_product_sku_dropdown")).first.click()
        page.wait_for_selector("[role='option']", timeout=10000)
        page.get_by_role("option", name=upload.product_sku, exact=True).first.click()
        _shot(page, self.screenshot_dir, "bulk_upload_step2_filled")

        # Click Upload — fall back to JS if a row-validation overlay blocks
        upload_btn = _locator(page, _require(self.selectors, "registrations.step2_upload_button")).first
        try:
            upload_btn.click(timeout=5000)
        except Exception:
            if not _js_click_button_by_text(page, "Upload"):
                raise
        _shot(page, self.screenshot_dir, "bulk_upload_after_upload_click")

        # Step 3: success indicator. The CRM can take several minutes to ingest a batch.
        success_indicator = _require(self.selectors, "registrations.import_complete_indicator")
        _locator(page, success_indicator).first.wait_for(state="visible", timeout=600_000)
        _shot(page, self.screenshot_dir, "bulk_upload_complete")

        # Close the dialog
        close_btn = self.selectors.get("registrations", {}).get("close_button")
        if close_btn:
            try:
                _locator(page, close_btn).first.click(timeout=3000)
            except Exception:
                pass

    def open_batch_by_po(self, po_number: str) -> None:
        """Open the batch we just created. Preferred path: navigate directly to the URL
        captured during create_batch (self._last_batch_url). Fallback: search the Plan's
        Batches table by PO number. The fallback is fragile because the table loads async
        and may not even show a PO Number column.
        """
        page = self._page

        last_url = getattr(self, "_last_batch_url", None)
        if last_url:
            self.logger.info("Opening batch by captured URL: %s", last_url)
            page.goto(last_url)
            page.wait_for_load_state("domcontentloaded")
            _shot(page, self.screenshot_dir, f"batch_opened_po_{_safe(po_number)}")
            return

        # Fallback: open the Batches tab, wait for the loading overlay to clear, filter
        # via the Search Batches input (the batches table does not expose a PO Number column
        # in prod, so substring-searching row text won't match — we must use the search box).
        plans_batches_tab = _require(self.selectors, "plan_detail.batches_tab")
        _locator(page, plans_batches_tab).first.click()
        target = (po_number or "").strip()

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
            self.logger.warning("'Getting Records...' overlay still present after 30s")
        page.wait_for_timeout(500)

        try:
            search = page.get_by_role("textbox", name="Search Batches...").first
            search.wait_for(state="visible", timeout=10000)
            search.fill("")
            search.fill(target)
            page.wait_for_timeout(1500)
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
            _shot(page, self.screenshot_dir, f"batches_filtered_{_safe(po_number)}")
        except Exception as exc:
            self.logger.warning("Search Batches input not usable: %s", exc)

        rows = page.get_by_role("row")
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.get_by_role("cell")
            if cells.count() < 1:
                continue
            txt = (cells.nth(0).inner_text() or "").strip()
            if not txt or "rows per page" in txt.lower():
                continue
            self.logger.info("Clicking batch row: %r", txt)
            cells.nth(0).click()
            _shot(page, self.screenshot_dir, f"batch_opened_po_{_safe(po_number)}")
            return
        _shot(page, self.screenshot_dir, f"FAILURE_batch_not_found_po_{_safe(po_number)}")
        raise RuntimeError(f"Batch with PO {po_number!r} not found in current Plan's batches")

    def create_transaction(self, txn: TransactionInput) -> None:
        """Open New Transaction (from a Batch detail), drive the 3-tab dialog.

        Tab 1: select-all pins (header checkbox toggles all rows).
        Tab 2: override Transaction Date and Effective Date (both default to today; both
               are react-datepicker inputs so they need the JS setter + close).
        Tab 3: click "Generate New Transaction" — that's the real submit. Wait for
               "Transaction successfully generated" alert.
        """
        page = self._page
        new_txn_btn = _require(self.selectors, "batch_detail.new_transaction_button")
        _locator(page, new_txn_btn).first.click()
        _shot(page, self.screenshot_dir, "new_transaction_dialog")

        # Tab 1: select all pins (header checkbox is the first checkbox in the dialog).
        # Native checkbox clicks via overlay-wrapped icons are unreliable; use JS.
        clicked = page.evaluate("""() => {
          const d = document.querySelector('[role="dialog"]');
          if (!d) return false;
          const cb = d.querySelector('input[type="checkbox"]');
          if (!cb) return false;
          cb.click();
          return true;
        }""")
        if not clicked:
            raise RuntimeError("Could not find select-all checkbox in transaction dialog")
        # Confirm count
        page.wait_for_function(
            "() => { const d = document.querySelector('[role=\"dialog\"]'); return d && /Selected Pin\\/s:\\s*\\d+\\s*Out Of\\s*\\d+/.test(d.innerText) && !/0\\s*Out Of/.test(d.innerText); }",
            timeout=15_000,
        )
        _shot(page, self.screenshot_dir, "txn_tab1_pins_selected")

        # Advance to Tab 2 and override dates
        _locator(page, _require(self.selectors, "transaction_form.next_button")).first.click()

        txn_date_css = _require(self.selectors, "transaction_form.transaction_date_input_css")
        eff_date_css = _require(self.selectors, "transaction_form.effective_date_input_css")
        _react_set_input(page, txn_date_css, txn.transaction_date)
        _react_close_datepicker(page, txn_date_css)
        _react_set_input(page, eff_date_css, txn.effective_date)
        _react_close_datepicker(page, eff_date_css)
        _shot(page, self.screenshot_dir, "txn_tab2_dates_set")

        # Advance to Tab 3 (review) — if the dialog is already on the final step the button
        # will be labeled Generate; otherwise click Next first.
        next_btn = _locator(page, _require(self.selectors, "transaction_form.next_button")).first
        try:
            if next_btn.is_enabled(timeout=2000):
                next_btn.click()
        except Exception:
            pass

        # Generate
        generate_btn = _locator(page, _require(self.selectors, "transaction_form.generate_button")).first
        try:
            generate_btn.click(timeout=5000)
        except Exception:
            if not _js_click_button_by_text(page, "Generate New Transaction"):
                raise

        # Wait for success
        success_indicator = _require(self.selectors, "transaction_form.submit_success_indicator")
        _locator(page, success_indicator).first.wait_for(state="visible", timeout=120_000)
        _shot(page, self.screenshot_dir, "transaction_submitted")

    # -- helpers -----------------------------------------------------------

    def _fill_dropdown_or_text(self, dotted: str, value: str) -> None:
        """Try to fill a value into a select or a combobox/text input.

        Supports:
        - native <select> -> use select_option
        - any other element -> click, then click an option matching the value, falling back
          to typing the value and pressing Enter.
        """
        page = self._page
        selector = _require(self.selectors, dotted)
        loc = _locator(page, selector).first

        try:
            # Try native select first
            loc.select_option(label=value, timeout=2000)
            return
        except Exception:
            pass

        try:
            loc.click()
            option_sel = {"role": "option", "name": value}
            try:
                _locator(page, option_sel).first.click(timeout=4000)
                return
            except Exception:
                pass
            # Fall back to typing
            try:
                loc.fill(value)
                page.keyboard.press("Enter")
            except Exception:
                loc.type(value)
                page.keyboard.press("Enter")
        except Exception as exc:
            self.logger.error("Failed to fill dropdown %s with %r: %s", dotted, value, exc)
            raise


# ---- High-level orchestration helpers ------------------------------------


def screenshot_on_failure(page, screenshot_dir: Path, stage: str) -> Path | None:
    if page is None:
        return None
    try:
        return _shot(page, screenshot_dir, f"FAILURE_{stage}")
    except Exception:
        return None
