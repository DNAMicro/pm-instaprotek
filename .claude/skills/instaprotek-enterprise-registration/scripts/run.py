#!/usr/bin/env python3
"""End-to-end orchestrator for the InstaProtek enterprise registration workflow.

Run from the project root:

    python .claude/skills/instaprotek-enterprise-registration/scripts/run.py

Flags:
    --headed                  Launch Playwright with a visible browser
    --dry-run                 Validate + resolve models but do not touch the CRM or webhook
    --skip-webhook            Execute the run but do not post to RingCentral
    --refresh-brand-menu      Force a re-read of the CRM Brand menu instead of using the cache
    --verbose                 Verbose stdout logging
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Ensure the scripts/ directory is on sys.path so sibling imports work when run as a script.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from utils import (
    AUTH_DIR,
    CONFIG_DIR,
    FAILURES_DIR,
    INPUT_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    SKILL_DIR,
    Credentials,
    build_run_folder_name,
    discover_input_files,
    ensure_dependencies,
    format_date_iso,
    format_date_us,
    load_credentials,
    load_json,
    make_run_folder,
    save_json,
    setup_logger,
    utc_timestamp,
)


def main() -> int:
    args = _parse_args()

    # Bootstrap logger first so dependency install messages are captured.
    boot_logger = setup_logger(log_file=None, verbose=args.verbose)
    boot_logger.info("Starting InstaProtek registration run (headless=%s, dry_run=%s)", not args.headed, args.dry_run)

    try:
        ensure_dependencies(boot_logger)
    except Exception as exc:
        boot_logger.error("Dependency install failed: %s", exc)
        return 2

    # Load settings; apply CLI overrides
    settings = load_json(CONFIG_DIR / "settings.json")
    if args.company:
        settings.setdefault("crm", {})["company_name"] = args.company.strip()
        boot_logger.info("Using CRM company from --company: %r", settings["crm"]["company_name"])
    if args.plan:
        settings.setdefault("crm", {})["plan_name"] = args.plan.strip()
        boot_logger.info("Using CRM plan from --plan: %r", settings["crm"]["plan_name"])

    # Discover input files first — if this fails we can't compute a PO number for the folder.
    try:
        discovered = discover_input_files(INPUT_DIR)
    except Exception as exc:
        boot_logger.error("Input file discovery failed: %s", exc)
        _post_failure_no_run_folder(
            settings,
            stage="discover_files",
            reason=str(exc),
            details={"input_dir": str(INPUT_DIR)},
            skip_webhook=args.skip_webhook or args.skip_failure_webhook,
            logger=boot_logger,
        )
        return 1

    # Parse the PO so we can include the PO# in run-folder names.
    from parse_po import parse_purchase_order

    try:
        po = parse_purchase_order(discovered.po_pdf)
    except Exception as exc:
        boot_logger.error("PO parsing failed: %s", exc)
        _post_failure_no_run_folder(
            settings,
            stage="parse_po",
            reason=f"PO parsing exception: {exc}",
            details={"po_pdf": discovered.po_pdf.name, "traceback": traceback.format_exc()},
            skip_webhook=args.skip_webhook or args.skip_failure_webhook,
            logger=boot_logger,
        )
        return 1

    po_number = po.po_number
    run_folder_name = build_run_folder_name(po_number)
    run_timestamp = utc_timestamp()
    success_folder = PROCESSED_DIR / run_folder_name
    failure_folder = FAILURES_DIR / run_folder_name

    # We do not create either folder yet — we wait until we know success vs failure.
    log_file = success_folder / "run_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(log_file=log_file, verbose=args.verbose)
    logger.info("Run timestamp (UTC): %s", run_timestamp)
    logger.info("PO number: %s", po_number)
    logger.info("PO file: %s", discovered.po_pdf.name)
    logger.info("Registration file: %s", discovered.registration_file.name)

    try:
        return _run_pipeline(
            args=args,
            settings=settings,
            discovered=discovered,
            po=po,
            run_timestamp=run_timestamp,
            success_folder=success_folder,
            failure_folder=failure_folder,
            logger=logger,
        )
    except Exception as exc:
        logger.exception("Unhandled exception during run: %s", exc)
        # Move the log into the failure folder.
        try:
            failure_folder.mkdir(parents=True, exist_ok=True)
            if log_file.exists():
                shutil.move(str(log_file), str(failure_folder / "run_log.txt"))
            # Clean up the empty success folder if it was created.
            if success_folder.exists() and not any(success_folder.iterdir()):
                success_folder.rmdir()
        except Exception:
            pass
        _post_failure(
            settings=settings,
            po_number=po_number,
            stage="unhandled_exception",
            reason=str(exc),
            details={"traceback": traceback.format_exc()},
            failure_folder=failure_folder,
            run_timestamp=run_timestamp,
            skip_webhook=args.skip_webhook or args.skip_failure_webhook,
            logger=logger,
        )
        return 1


def _run_pipeline(
    *,
    args,
    settings,
    discovered,
    po,
    run_timestamp,
    success_folder,
    failure_folder,
    logger,
) -> int:
    # Load credentials (env selectable via --env flag; defaults to credentials.json's "Env" field)
    try:
        credentials = load_credentials(env=args.env)
    except Exception as exc:
        _fail(
            stage="load_credentials",
            reason=str(exc),
            details={"env_requested": args.env},
            success_folder=success_folder,
            failure_folder=failure_folder,
            settings=settings,
            po=po,
            run_timestamp=run_timestamp,
            skip_webhook=args.skip_webhook or args.skip_failure_webhook,
            logger=logger,
        )
        return 1
    logger.info("Loaded credentials for env=%s", credentials.env)

    # If the env block specified a CRM base URL, it overrides settings.json
    if credentials.crm_base_url:
        prior = settings.get("crm", {}).get("base_url")
        settings.setdefault("crm", {})["base_url"] = credentials.crm_base_url
        logger.info("CRM base_url from credentials env %r: %r (was %r)",
                    credentials.env, credentials.crm_base_url, prior)

    # Load + validate the registration file
    from validate_inputs import (
        load_registration_file,
        validate_and_clean,
        write_cleaned_and_preserved,
    )

    try:
        reg = load_registration_file(discovered.registration_file)
    except Exception as exc:
        _fail(
            stage="load_registration",
            reason=str(exc),
            details={"file": discovered.registration_file.name},
            success_folder=success_folder,
            failure_folder=failure_folder,
            settings=settings,
            po=po,
            run_timestamp=run_timestamp,
            skip_webhook=args.skip_webhook or args.skip_failure_webhook,
            logger=logger,
        )
        return 1

    validation = validate_and_clean(
        reg,
        po,
        sku_pattern=settings["validation"].get("sku_pattern"),
        auto_trim=settings["validation"].get("auto_trim_whitespace", True),
        auto_yes_no=settings["validation"].get("auto_normalize_yes_no", True),
        auto_titlecase_manufacturer=settings["validation"].get("auto_titlecase_manufacturer", True),
    )
    logger.info(
        "Validation: %d rows, %d auto-fixes, %d rows flagged for model resolution. errors=%s warnings=%s",
        reg.row_count,
        len(validation.fixes_applied),
        len(validation.rows_needing_model_resolution),
        len(validation.errors),
        len(validation.warnings),
    )

    if validation.has_errors:
        _fail(
            stage="validate",
            reason="; ".join(validation.errors),
            details={
                "cross_validation": validation.cross_validation,
                "warnings": validation.warnings,
            },
            success_folder=success_folder,
            failure_folder=failure_folder,
            settings=settings,
            po=po,
            run_timestamp=run_timestamp,
            skip_webhook=args.skip_webhook or args.skip_failure_webhook,
            logger=logger,
        )
        return 1

    # ---- Brand catalog + model resolution ----
    # Decide whether we need Playwright at all. If --dry-run AND the brand cache is fresh
    # AND there are no rows needing resolution, we can skip the browser entirely.
    brand_cache_path = CONFIG_DIR / "brand_menu_cache.json"
    brand_cache = (
        load_json(brand_cache_path)
        if brand_cache_path.exists()
        else {"fetched_at": None, "brands": [], "devices_by_brand": {}}
    )
    brand_cache_fresh = _brand_cache_fresh(brand_cache, settings)
    need_brand_refresh = args.refresh_brand_menu or not brand_cache_fresh

    brand_names: list[str] = list(brand_cache.get("brands") or [])
    devices_by_brand: dict[str, list[str]] = dict(brand_cache.get("devices_by_brand") or {})

    crm_runner = None
    if args.dry_run and not need_brand_refresh and not validation.rows_needing_model_resolution:
        logger.info("Dry-run with no resolution needed and fresh brand cache — skipping Playwright entirely.")
    else:
        # Launch Playwright; login; optionally refresh brand menu.
        from playwright_runner import CRMRunner

        selectors_path = CONFIG_DIR / "selectors.json"
        selectors = load_json(selectors_path)
        screenshot_dir = success_folder / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        storage_state_path = AUTH_DIR / "storage_state.json"
        headless = not args.headed

        try:
            with CRMRunner(
                settings=settings,
                selectors=selectors,
                credentials=credentials,
                headless=headless,
                screenshot_dir=screenshot_dir,
                storage_state_path=storage_state_path,
                logger=logger,
            ) as runner:
                try:
                    runner.login()
                except Exception as exc:
                    logger.exception("Login failed: %s", exc)
                    _fail(
                        stage="playwright_login",
                        reason=str(exc),
                        details={"traceback": traceback.format_exc()},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1

                if need_brand_refresh:
                    try:
                        brand_names = runner.read_brand_list()
                        # Device lists are lazy — clear the cache when the brand list refreshes
                        # so stale entries are not used against the new catalog.
                        devices_by_brand = {}
                        brand_cache = {
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                            "source_url": settings["crm"]["base_url"],
                            "brands": brand_names,
                            "devices_by_brand": devices_by_brand,
                        }
                        save_json(brand_cache_path, brand_cache)
                    except Exception as exc:
                        logger.exception("Brand list read failed: %s", exc)
                        _fail(
                            stage="read_brand_list",
                            reason=str(exc),
                            details={"traceback": traceback.format_exc()},
                            success_folder=success_folder,
                            failure_folder=failure_folder,
                            settings=settings,
                            po=po,
                            run_timestamp=run_timestamp,
                            skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                            logger=logger,
                        )
                        return 1

                # ---- Resolve model names against the live Brand -> Device catalog ----
                resolution_report = _resolve_models(
                    reg=reg,
                    validation=validation,
                    brand_names=brand_names,
                    devices_by_brand=devices_by_brand,
                    runner=runner,
                    brand_cache_path=brand_cache_path,
                    brand_cache=brand_cache,
                    settings=settings,
                    logger=logger,
                )

                if resolution_report.unresolved:
                    _fail(
                        stage="resolve_models",
                        reason=f"{len(resolution_report.unresolved)} row(s) could not be reconciled to the Brand menu",
                        details={"unresolved": [
                            {
                                "row": o.row,
                                "manufacturer": o.original_manufacturer,
                                "model_number": o.original_model_number,
                                "search_query": o.search_query,
                                "search_candidate": o.search_candidate,
                                "search_source_url": o.search_source_url,
                                "error": o.error,
                            }
                            for o in resolution_report.unresolved
                        ]},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1

                # Write cleaned + preserved registration files into the success folder.
                cleaned_path, original_copy_path = write_cleaned_and_preserved(
                    reg,
                    destination_folder=success_folder,
                    original_source=discovered.registration_file,
                )
                logger.info("Cleaned registration written to %s", cleaned_path)
                logger.info("Original preserved at %s", original_copy_path)

                # Write the validation + resolution reports
                save_json(
                    success_folder / "validation_report.json",
                    {
                        "fixes_applied": validation.fixes_applied,
                        "cross_validation": validation.cross_validation,
                        "warnings": validation.warnings,
                        "model_resolution": [
                            {
                                "row": o.row,
                                "original_manufacturer": o.original_manufacturer,
                                "original_model_number": o.original_model_number,
                                "resolved_manufacturer": o.resolved_manufacturer,
                                "resolved_model_number": o.resolved_model_number,
                                "method": o.method,
                                "search_query": o.search_query,
                                "search_candidate": o.search_candidate,
                                "search_source_url": o.search_source_url,
                            }
                            for o in resolution_report.outcomes
                        ],
                    },
                )

                if args.dry_run:
                    logger.info("Dry-run: skipping CRM batch/upload/transaction and webhook.")
                    _move_inputs_into_folder(discovered, success_folder, logger, copy_only=True)
                    # In dry-run we still report success so the operator can confirm what would have been submitted.
                    logger.info("Dry-run complete.")
                    return 0

                # ---- Step 2: batch ----
                from playwright_runner import BatchInput, BulkUploadInput, TransactionInput

                plan_purchase_date_us = format_date_us(po.order_date)
                transaction_date_us = plan_purchase_date_us
                # Effective date = delivery date from CSV first row
                delivery_date_raw = reg.rows[0].get("Delivery Date") if reg.rows else None
                from utils import parse_date_flexible

                effective_dt = parse_date_flexible(delivery_date_raw)
                effective_date_us = format_date_us(effective_dt)

                if not plan_purchase_date_us:
                    _fail(
                        stage="resolve_dates",
                        reason="PO order date could not be parsed.",
                        details={"po": po.to_dict()},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1
                if not effective_date_us:
                    _fail(
                        stage="resolve_dates",
                        reason="CSV Delivery Date could not be parsed for the first row.",
                        details={"first_row": reg.rows[0] if reg.rows else None},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1

                # Resolve the product SKU. --product-sku flag wins; otherwise consult the
                # references price list using the PO rate.
                sku_hint = ""
                if args.product_sku:
                    sku_hint = args.product_sku.strip()
                    logger.info("Using product SKU from --product-sku flag: %r (skipping references lookup)", sku_hint)
                else:
                    from utils import lookup_sku_by_price

                    if po.rate is not None:
                        sku_result = lookup_sku_by_price(po.rate)
                        if sku_result:
                            sku_hint, sku_product_name = sku_result
                            logger.info(
                                "Reference lookup: rate=%.2f -> SKU=%r (%s)",
                                po.rate, sku_hint, sku_product_name,
                            )
                        else:
                            logger.warning(
                                "No SKU found in reference file for rate %.2f — will auto-select first product",
                                po.rate,
                            )

                batch = BatchInput(
                    product_label="",
                    number_of_pins=reg.row_count,
                    po_number=po.po_number or "",
                    plan_purchase_date=plan_purchase_date_us,
                    plan_purchase_price=f"{po.rate:.2f}" if po.rate is not None else "0.00",
                    vertical=settings["crm"].get("default_vertical", "Education"),
                    invoice_number="",
                    product_sku_hint=sku_hint,
                )

                batch_result: dict[str, str] = {}
                try:
                    # Plan name: --plan flag wins, then settings.json crm.plan_name, then PO description
                    # (last one usually doesn't match the CRM and will hard-fail clean).
                    plan_name_for_run = (
                        settings["crm"].get("plan_name")
                        or settings["crm"].get("default_plan_name")
                        or po.plan_description
                        or ""
                    )
                    runner.open_company_and_plan(
                        settings["crm"].get("company_name", "Demo Company"),
                        plan_name_for_run,
                    )
                    batch_result = runner.create_batch(batch) or {}
                    logger.info("Batch created: product_label=%r product_sku=%r",
                                batch_result.get("product_label"), batch_result.get("product_sku"))
                except Exception as exc:
                    logger.exception("Batch creation failed: %s", exc)
                    _fail(
                        stage="create_batch",
                        reason=str(exc),
                        details={"traceback": traceback.format_exc(), "batch": batch.__dict__},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1

                # ---- Step 3: CSV upload ----
                product_sku_for_upload = batch_result.get("product_sku", "")
                if not product_sku_for_upload:
                    _fail(
                        stage="import_csv",
                        reason="Could not extract Product SKU from the Batch's Product dropdown option. "
                               "Step 2 of Bulk Upload requires the SKU/barcode.",
                        details={"batch_result": batch_result},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1
                try:
                    runner.import_csv(BulkUploadInput(
                        file_path=cleaned_path,
                        company_name=settings["crm"].get("company_name", "Demo Company"),
                        product_sku=product_sku_for_upload,
                    ))
                except Exception as exc:
                    logger.exception("CSV import failed: %s", exc)
                    _fail(
                        stage="import_csv",
                        reason=str(exc),
                        details={"traceback": traceback.format_exc(), "file": str(cleaned_path)},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1

                # ---- Step 4: transaction ----
                # After upload we're back on /portal/registration; re-navigate to the batch
                # we just created (lookup by PO number) before opening New Transaction.
                txn = TransactionInput(
                    transaction_date=transaction_date_us,
                    effective_date=effective_date_us,
                )
                try:
                    runner.open_company_and_plan(
                        settings["crm"].get("company_name", "Demo Company"),
                        plan_name_for_run,
                    )
                    runner.open_batch_by_po(po.po_number or "")
                    runner.create_transaction(txn)
                except Exception as exc:
                    logger.exception("Transaction submission failed: %s", exc)
                    _fail(
                        stage="create_transaction",
                        reason=str(exc),
                        details={"traceback": traceback.format_exc(), "transaction": txn.__dict__},
                        success_folder=success_folder,
                        failure_folder=failure_folder,
                        settings=settings,
                        po=po,
                        run_timestamp=run_timestamp,
                        skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                        logger=logger,
                    )
                    return 1

        except Exception as exc:
            logger.exception("Playwright session failed: %s", exc)
            _fail(
                stage="playwright_session",
                reason=str(exc),
                details={"traceback": traceback.format_exc()},
                success_folder=success_folder,
                failure_folder=failure_folder,
                settings=settings,
                po=po,
                run_timestamp=run_timestamp,
                skip_webhook=args.skip_webhook or args.skip_failure_webhook,
                logger=logger,
            )
            return 1

    # ---- Step 5: webhook ----
    auto_fixed_rows_count = len({fix["row"] for fix in validation.fixes_applied})
    flagged_rows_count = 0  # zero by design — we hard-fail on unresolved rows

    from send_webhook import SuccessPayload, post_success

    success_payload = SuccessPayload(
        po_number=po.po_number,
        company=settings["crm"].get("company_name", "Demo Company"),
        plan=po.plan_description,
        pin_count=reg.row_count,
        end_user=po.end_user.name if po.end_user else None,
        transaction_date=format_date_iso(po.order_date),
        effective_date=format_date_iso(_first_delivery_date(reg)),
        auto_fixed_rows=auto_fixed_rows_count,
        flagged_rows=flagged_rows_count,
        processed_folder=str(success_folder.relative_to(PROJECT_ROOT)),
        run_timestamp=run_timestamp,
        crm_url=settings["crm"]["base_url"],
    )

    if args.skip_webhook:
        logger.info("Skipping webhook post per --skip-webhook flag.")
    else:
        webhook_response = post_success(
            settings["webhook"]["url"],
            success_payload,
            save_to=success_folder / "webhook_response.json",
            timeout_seconds=settings["webhook"].get("timeout_seconds", 15),
        )
        logger.info("Webhook response: %s", webhook_response.get("status_code"))

    # ---- Move inputs into the success folder ----
    _move_inputs_into_folder(discovered, success_folder, logger, copy_only=False)

    logger.info("Run complete. Output: %s", success_folder)
    return 0


# ---- Helpers --------------------------------------------------------------


def _brand_cache_fresh(cache: dict[str, Any], settings: dict[str, Any]) -> bool:
    ts = cache.get("fetched_at")
    if not ts:
        return False
    try:
        fetched = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else None
    except Exception:
        return False
    if fetched is None:
        return False
    max_age_hours = settings.get("brand_menu_cache", {}).get("max_age_hours", 168)
    age = datetime.now(timezone.utc) - fetched
    return age <= timedelta(hours=max_age_hours)


def _resolve_models(
    reg, validation, *,
    brand_names: list[str],
    devices_by_brand: dict[str, list[str]],
    runner,
    brand_cache_path: Path,
    brand_cache: dict[str, Any],
    settings,
    logger,
):
    """Wire up the searcher + device fetcher, then run resolve_rows.

    Devices are fetched lazily — only brands touched during resolution get scraped. After
    each lazy fetch the on-disk brand cache is updated so subsequent runs can skip the work.
    """
    from resolve_model_names import (
        CrmCatalog,
        DeviceFetcher,
        load_sku_cache,
        resolve_rows,
        save_sku_cache,
    )
    from utils import collapse_ws

    sku_cache_path = CONFIG_DIR / "sku_to_model.json"
    sku_cache = load_sku_cache(sku_cache_path)

    searcher = _build_searcher(settings, logger)

    catalog = CrmCatalog.from_names(brand_names)
    # Hydrate the catalog from any cached per-brand device lists so we don't re-scrape.
    for brand_key, devices in (devices_by_brand or {}).items():
        catalog.preload_devices(brand_key, devices)

    class _LiveDeviceFetcher:
        """Drives the Playwright runner to scrape devices for a brand on first request,
        then persists the result to brand_menu_cache.json so it's reused next run."""

        def fetch(self, brand_name: str) -> list[str]:
            try:
                devices = runner.read_devices_for_brand(brand_name)
            except Exception as exc:
                logger.warning("Device fetch failed for brand %r: %s", brand_name, exc)
                return []
            devices_by_brand[collapse_ws(brand_name).lower()] = devices
            brand_cache["devices_by_brand"] = devices_by_brand
            try:
                save_json(brand_cache_path, brand_cache)
            except Exception as exc:
                logger.warning("Could not persist updated brand cache: %s", exc)
            return devices

    report = resolve_rows(
        rows=reg.rows,
        rows_needing_resolution=validation.rows_needing_model_resolution,
        catalog=catalog,
        device_fetcher=_LiveDeviceFetcher(),
        sku_cache=sku_cache,
        web_searcher=searcher,
        search_query_template=settings["search"]["query_template"],
        min_confidence=settings["search"].get("min_confidence", 0.75),
        on_log=lambda msg: logger.info("[resolver] %s", msg),
    )
    save_sku_cache(sku_cache_path, sku_cache)
    return report


def _build_searcher(settings, logger):
    """Create a minimal-dependency web searcher.

    The searcher hits Google's HTML search endpoint and extracts a candidate model name from
    the result snippets. It is deliberately conservative: if Google blocks the request or the
    response has no recognizable candidates, search returns an empty list and the row will
    fail validation.
    """
    import re as _re
    import requests as _requests

    from resolve_model_names import SearchResult

    UA = settings["playwright"].get("user_agent", "Mozilla/5.0")

    class GoogleHtmlSearcher:
        def search(self, query: str):
            url = "https://www.google.com/search"
            try:
                r = _requests.get(
                    url,
                    params={"q": query, "hl": "en", "num": 10},
                    headers={
                        "User-Agent": UA,
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                    timeout=15,
                )
            except Exception as exc:
                logger.warning("Google search request failed: %s", exc)
                return []
            if r.status_code != 200:
                logger.warning("Google search returned status %s", r.status_code)
                return []

            html = r.text
            results: list[SearchResult] = []

            # Heuristic 1: look for a "Model Name: <X>" pattern in the snippet area.
            for match in _re.finditer(r"Model\s*Name[:\s]+([A-Za-z0-9 +\-./]+)", html, _re.IGNORECASE):
                candidate = match.group(1).strip()
                # Strip trailing fluff (".", words like "Storage", "Color")
                candidate = _re.sub(r"\s+(Storage|Color|Carrier|Released|RAM)\b.*$", "", candidate, flags=_re.IGNORECASE)
                candidate = candidate.strip(" .,-")
                if candidate:
                    results.append(SearchResult(candidate=candidate, source_url=r.url, snippet="Model Name match", confidence=0.95))

            # Heuristic 2: look for "<manufacturer> Galaxy <model>" or similar patterns near the query terms.
            # We strip HTML tags first.
            text = _re.sub(r"<[^>]+>", " ", html)
            text = _re.sub(r"\s+", " ", text)
            # Look for "is the <X>," patterns from AI Overview style answers.
            for match in _re.finditer(r"is\s+the\s+([A-Z][A-Za-z0-9 +\-./]+?)(?:[,.]|\s+specifically)", text):
                candidate = match.group(1).strip()
                if 4 <= len(candidate) <= 80:
                    results.append(SearchResult(candidate=candidate, source_url=r.url, snippet="AI Overview pattern", confidence=0.85))

            # Deduplicate by candidate string
            seen: set[str] = set()
            deduped: list[SearchResult] = []
            for res in results:
                key = res.candidate.lower()
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(res)
            return deduped

    return GoogleHtmlSearcher()


def _first_delivery_date(reg):
    from utils import parse_date_flexible

    if not reg.rows:
        return None
    return parse_date_flexible(reg.rows[0].get("Delivery Date"))


def _move_inputs_into_folder(discovered, dest_folder: Path, logger, *, copy_only: bool) -> None:
    dest_folder.mkdir(parents=True, exist_ok=True)
    for src in (discovered.po_pdf,):
        target = dest_folder / src.name
        if copy_only:
            shutil.copy2(src, target)
            logger.info("Copied %s -> %s", src.name, target)
        else:
            shutil.move(str(src), str(target))
            logger.info("Moved %s -> %s", src.name, target)

    # The registration file: if a cleaned copy already exists under the same name in dest_folder,
    # we do NOT overwrite it (the cleaned file is what we want). The original is preserved alongside
    # by validate_inputs.write_cleaned_and_preserved with the .original suffix.
    src = discovered.registration_file
    target = dest_folder / src.name
    if not target.exists():
        if copy_only:
            shutil.copy2(src, target)
        else:
            shutil.move(str(src), str(target))
        logger.info("%s registration file -> %s", "Copied" if copy_only else "Moved", target)
    else:
        # Cleaned version is already at this path. Remove the source from input/ (unless dry-run).
        if not copy_only:
            try:
                src.unlink()
                logger.info("Removed source registration from input/: %s", src.name)
            except Exception as exc:
                logger.warning("Could not remove %s from input/: %s", src, exc)


def _fail(
    *,
    stage,
    reason,
    details,
    success_folder: Path,
    failure_folder: Path,
    settings,
    po,
    run_timestamp,
    skip_webhook,
    logger,
):
    logger.error("FAILURE [%s]: %s", stage, reason)
    failure_folder.mkdir(parents=True, exist_ok=True)
    # Move any partial outputs (screenshots, validation reports, log) into the failure folder.
    for entry in list(success_folder.iterdir()) if success_folder.exists() else []:
        target = failure_folder / entry.name
        try:
            if target.exists():
                # Avoid collision; suffix with a counter
                i = 1
                while target.exists():
                    target = failure_folder / f"{entry.stem}_{i}{entry.suffix}"
                    i += 1
            shutil.move(str(entry), str(target))
        except Exception as exc:
            logger.warning("Could not move %s into failure folder: %s", entry, exc)
    if success_folder.exists() and not any(success_folder.iterdir()):
        try:
            success_folder.rmdir()
        except Exception:
            pass

    _post_failure(
        settings=settings,
        po_number=getattr(po, "po_number", None),
        stage=stage,
        reason=reason,
        details=details,
        failure_folder=failure_folder,
        run_timestamp=run_timestamp,
        skip_webhook=skip_webhook,
        logger=logger,
    )


def _post_failure(
    *,
    settings,
    po_number,
    stage,
    reason,
    details,
    failure_folder: Path,
    run_timestamp,
    skip_webhook,
    logger,
):
    if skip_webhook:
        logger.info("Skipping failure webhook post per --skip-webhook flag.")
        return
    from send_webhook import FailurePayload, post_failure

    payload = FailurePayload(
        po_number=po_number,
        stage=stage,
        reason=reason,
        details=details,
        failed_folder=str(failure_folder.relative_to(PROJECT_ROOT)) if failure_folder else None,
        run_timestamp=run_timestamp,
    )
    save_to = failure_folder / "webhook_response.json" if failure_folder else None
    try:
        post_failure(
            settings["webhook"]["url"],
            payload,
            save_to=save_to,
            timeout_seconds=settings["webhook"].get("timeout_seconds", 15) * 2,
        )
    except Exception as exc:
        logger.error("Failed to post failure webhook: %s", exc)


def _post_failure_no_run_folder(
    settings,
    *,
    stage,
    reason,
    details,
    skip_webhook,
    logger,
):
    """For failures so early we never built a run folder."""
    if skip_webhook:
        logger.info("Skipping failure webhook post per --skip-webhook flag.")
        return
    from send_webhook import FailurePayload, post_failure

    payload = FailurePayload(
        po_number=None,
        stage=stage,
        reason=reason,
        details=details,
        failed_folder=None,
        run_timestamp=utc_timestamp(),
    )
    try:
        post_failure(
            settings["webhook"]["url"],
            payload,
            save_to=None,
            timeout_seconds=settings["webhook"].get("timeout_seconds", 15) * 2,
        )
    except Exception as exc:
        logger.error("Failed to post failure webhook: %s", exc)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="InstaProtek enterprise registration orchestrator")
    p.add_argument("--headed", action="store_true", help="Launch Playwright with a visible browser")
    p.add_argument("--dry-run", action="store_true", help="Validate + resolve only; do not touch CRM or webhook")
    p.add_argument("--skip-webhook", action="store_true", help="Do not post to RingCentral (success or failure)")
    p.add_argument(
        "--skip-failure-webhook",
        action="store_true",
        help="Suppress only failure webhook posts; still post success webhook on a successful run.",
    )
    p.add_argument("--refresh-brand-menu", action="store_true", help="Force a re-read of the CRM Brand menu")
    p.add_argument("--verbose", action="store_true", help="Verbose stdout logging")
    p.add_argument(
        "--company",
        default=None,
        help=(
            "CRM company name for this run (e.g. \"Demo Company\" for QA, "
            "\"Connected Solutions Group, LLC.\" for production). Overrides "
            "settings.json crm.company_name when provided."
        ),
    )
    p.add_argument(
        "--plan",
        default=None,
        help=(
            "CRM plan name to attach this batch to (e.g. \"Extended Service Contract - 12 Months\"). "
            "Required when PO plan description doesn't match the CRM plan verbatim. Overrides "
            "settings.json crm.default_plan_name when provided. If unset, falls back to the PO's "
            "plan_description, which usually does NOT match the CRM plan."
        ),
    )
    p.add_argument(
        "--env",
        default=None,
        help=(
            "Which environment block in credentials.json to use (case-insensitive). "
            "Typical values: \"QA\" (default) or \"Production\". Overrides the 'Env' field "
            "in credentials.json. The env's crm_base_url (if set) overrides settings.json crm.base_url."
        ),
    )
    p.add_argument(
        "--product-sku",
        default=None,
        help=(
            "Product SKU / barcode (e.g. \"ESC030012MO00IK\") to pick in the New Batch dialog. "
            "When provided, bypasses the references-folder price lookup entirely."
        ),
    )
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(main())
