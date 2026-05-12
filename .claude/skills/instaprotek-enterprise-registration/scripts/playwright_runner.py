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
    product_label: str               # Plan / product name from PO
    number_of_pins: int
    po_number: str
    plan_purchase_date: str          # "MM/DD/YYYY"
    vertical: str                    # "Education"


@dataclass
class TransactionInput:
    transaction_date: str            # "MM/DD/YYYY" — from PO
    effective_date: str              # "MM/DD/YYYY" — from CSV delivery date


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

    def open_company_and_plan(self, plan_name: str) -> None:
        page = self._page
        # Navigate Settings -> Company -> Demo Company
        settings_nav = _require(self.selectors, "settings.settings_nav")
        company_link = _require(self.selectors, "settings.company_link")
        company_picker = self.selectors.get("company", {}).get("company_picker") or ""
        demo_option = _require(self.selectors, "company.demo_company_option")

        _locator(page, settings_nav).first.click()
        _locator(page, company_link).first.click()
        if company_picker:
            _locator(page, company_picker).first.click()
        _locator(page, demo_option).first.click()
        _shot(page, self.screenshot_dir, "company_selected")

        # Plans tab + plan row
        plans_tab = _require(self.selectors, "company.plans_tab")
        plan_row_template = _require(self.selectors, "company.plan_row_by_name")

        _locator(page, plans_tab).first.click()
        if isinstance(plan_row_template, str):
            sel = plan_row_template.replace("{plan_name}", plan_name)
        elif isinstance(plan_row_template, dict) and "text" in plan_row_template:
            sel = {"text": plan_name, "exact": True}
        else:
            sel = plan_row_template
        _locator(page, sel).first.click()
        _shot(page, self.screenshot_dir, "plan_selected")

    def create_batch(self, batch: BatchInput) -> None:
        page = self._page
        new_batch_btn = _require(self.selectors, "company.new_batch_button")
        _locator(page, new_batch_btn).first.click()
        _shot(page, self.screenshot_dir, "new_batch_dialog")

        # Fill batch form
        self._fill_dropdown_or_text("batch_form.product_dropdown", batch.product_label)
        _locator(page, _require(self.selectors, "batch_form.number_of_pins_input")).first.fill(
            str(batch.number_of_pins)
        )
        _locator(page, _require(self.selectors, "batch_form.po_number_input")).first.fill(
            batch.po_number
        )
        _locator(page, _require(self.selectors, "batch_form.plan_purchase_date_input")).first.fill(
            batch.plan_purchase_date
        )
        self._fill_dropdown_or_text("batch_form.vertical_dropdown", batch.vertical)
        _shot(page, self.screenshot_dir, "batch_filled")

        _locator(page, _require(self.selectors, "batch_form.save_and_continue_button")).first.click()
        _shot(page, self.screenshot_dir, "batch_saved")

    def import_csv(self, file_path: Path) -> None:
        page = self._page
        registrations_nav = _require(self.selectors, "registrations.registrations_nav")
        import_btn = _require(self.selectors, "registrations.import_csv_button")
        file_input = _require(self.selectors, "registrations.file_input")
        complete_indicator = _require(self.selectors, "registrations.import_complete_indicator")

        _locator(page, registrations_nav).first.click()
        _locator(page, import_btn).first.click()
        _locator(page, file_input).first.set_input_files(str(file_path))
        _shot(page, self.screenshot_dir, "csv_upload_started")
        _locator(page, complete_indicator).first.wait_for(state="visible", timeout=120_000)
        _shot(page, self.screenshot_dir, "csv_upload_complete")

    def create_transaction(self, txn: TransactionInput) -> None:
        page = self._page
        new_txn_btn = _require(self.selectors, "company.new_transaction_button")
        _locator(page, new_txn_btn).first.click()
        _shot(page, self.screenshot_dir, "new_transaction_dialog")

        _locator(page, _require(self.selectors, "transaction_form.transaction_date_input")).first.fill(
            txn.transaction_date
        )
        _locator(page, _require(self.selectors, "transaction_form.effective_date_input")).first.fill(
            txn.effective_date
        )
        # Select all rows + submit
        _locator(page, _require(self.selectors, "transaction_form.select_all_checkbox")).first.check()
        _shot(page, self.screenshot_dir, "transaction_filled")

        _locator(page, _require(self.selectors, "transaction_form.submit_button")).first.click()
        _locator(page, _require(self.selectors, "transaction_form.submit_success_indicator")).first.wait_for(
            state="visible", timeout=120_000
        )
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
