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
    # product_label: leave empty to auto-select the only option in the Product dropdown
    # (most Plans have exactly one Product). Provide a specific label only if the dropdown
    # offers multiple options and the caller knows which to pick.
    product_label: str
    number_of_pins: int
    po_number: str
    plan_purchase_date: str          # "MM/DD/YYYY"
    plan_purchase_price: str         # e.g. "14.43" — PO unit rate; field is required by the CRM
    vertical: str                    # "Education" etc. — see CRM Vertical dropdown options
    invoice_number: str = ""         # optional


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
        page.goto(base + login_path)
        _shot(page, self.screenshot_dir, "login_loaded")

        # If a post-login indicator is already present, skip the login form (storage state restored).
        try:
            indicator = _require(self.selectors, "login.post_login_indicator")
            if _locator(page, indicator).first.is_visible(timeout=2000):
                self.logger.info("Already logged in (session restored from storage state).")
                return
        except SelectorMissing:
            pass
        except Exception:
            pass

        username_sel = _require(self.selectors, "login.username_input")
        password_sel = _require(self.selectors, "login.password_input")
        submit_sel = _require(self.selectors, "login.submit_button")
        indicator_sel = _require(self.selectors, "login.post_login_indicator")

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
        page.wait_for_timeout(500)  # filter debounce
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
        page.wait_for_timeout(500)

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
        _shot(page, self.screenshot_dir, f"company_selected_{_safe(company_name)}")

        # Plans tab + plan row
        plans_tab = _require(self.selectors, "company.plans_tab")
        _locator(page, plans_tab).first.click()
        _locator(page, plans_tab).first.wait_for(state="visible")

        # Optional: narrow the plan list via search if the input exists in the selectors
        plans_search = self.selectors.get("company", {}).get("plans_search_input")
        if plans_search:
            try:
                ploc = _locator(page, plans_search).first
                ploc.fill("")
                ploc.fill(plan_name)
                page.wait_for_timeout(400)
            except Exception:
                pass

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
        new_batch_btn = _require(self.selectors, "company.new_batch_button")
        _locator(page, new_batch_btn).first.click()
        _shot(page, self.screenshot_dir, "new_batch_dialog")

        # Product — auto-pick the only option when no label specified. We capture the chosen
        # option's accessible name so the caller can extract the SKU for the later CSV upload
        # (option name format observed: "Accidental Damage Replacement - 12 Months (ESC030012MO00IK)").
        product_dropdown = _require(self.selectors, "batch_form.product_dropdown")
        _locator(page, product_dropdown).first.click()
        chosen_option = (
            _locator(page, {"role": "option", "name": batch.product_label}).first
            if batch.product_label
            else _locator(page, {"role": "option"}).first
        )
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

        # Plan Purchase Date — react-datepicker workaround
        date_css = _require(self.selectors, "batch_form.plan_purchase_date_input_css")
        _react_set_input(page, date_css, batch.plan_purchase_date)
        _react_close_datepicker(page, date_css)

        # Vertical — open dropdown, click option
        _locator(page, _require(self.selectors, "batch_form.vertical_dropdown")).first.click()
        _locator(page, {"role": "option", "name": batch.vertical}).first.click()

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

        # Pull the product SKU out of the option label (last "(...)" group)
        import re as _re
        sku_match = _re.search(r"\(([^()]+)\)\s*$", chosen_product_label)
        product_sku = sku_match.group(1) if sku_match else ""
        return {"product_label": chosen_product_label, "product_sku": product_sku}

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

        # Step 2: Company + Product SKU
        _locator(page, _require(self.selectors, "registrations.step2_company_dropdown")).first.click()
        _locator(page, {"role": "option", "name": upload.company_name}).first.click()

        _locator(page, _require(self.selectors, "registrations.step2_product_sku_dropdown")).first.click()
        _locator(page, {"role": "option", "name": upload.product_sku}).first.click()
        _shot(page, self.screenshot_dir, "bulk_upload_step2_filled")

        # Click Upload — fall back to JS if a row-validation overlay blocks
        upload_btn = _locator(page, _require(self.selectors, "registrations.step2_upload_button")).first
        try:
            upload_btn.click(timeout=5000)
        except Exception:
            if not _js_click_button_by_text(page, "Upload"):
                raise

        # Step 3: success indicator
        success_indicator = _require(self.selectors, "registrations.import_complete_indicator")
        _locator(page, success_indicator).first.wait_for(state="visible", timeout=180_000)
        _shot(page, self.screenshot_dir, "bulk_upload_complete")

        # Close the dialog
        close_btn = self.selectors.get("registrations", {}).get("close_button")
        if close_btn:
            try:
                _locator(page, close_btn).first.click(timeout=3000)
            except Exception:
                pass

    def open_batch_by_po(self, po_number: str) -> None:
        """Find the batch we just created (by PO Number) in the current Plan's Batches tab
        and click into it. Must be called when the Plan Details modal/page is visible."""
        page = self._page
        plans_batches_tab = _require(self.selectors, "plan_detail.batches_tab")
        _locator(page, plans_batches_tab).first.click()
        # Find the row whose PO Number cell equals po_number; click the Batch Number cell.
        target = (po_number or "").strip()
        rows = page.get_by_role("row")
        for i in range(rows.count()):
            row = rows.nth(i)
            row_text = (row.inner_text() or "").strip()
            if target and target in row_text:
                cells = row.get_by_role("cell")
                if cells.count() >= 1:
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
