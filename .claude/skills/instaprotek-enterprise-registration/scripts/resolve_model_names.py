"""Reconcile each registration row's (Manufacturer, Model Number) against the CRM's
Brand -> Devices hierarchy.

The CRM stores models in two levels:

    Brand (e.g. "Samsung Galaxy")
        |- Device (e.g. "A15 5G")

When a row's (Manufacturer, Model Number) does not match an existing (Brand, Device) pair,
BOTH cells get rewritten to the exact CRM strings before upload.

Resolution order for each row:
    1. Direct (Brand, Device) match: if Manufacturer == some Brand name AND Model Number ==
       some Device name under that Brand, normalize casing and continue.
    2. Persistent SKU cache (config/sku_to_model.json), validated against the live catalog.
    3. Web search "<Manufacturer> <Model Number> model name". The search candidate (e.g.
       "Samsung Galaxy A15 5G") is split using the longest Brand-name prefix in the
       catalog; the remainder is the device-name candidate, which must exist exactly in
       that Brand's Devices list.
    4. Otherwise the row is unresolved -> hard-fail at the orchestrator level.

Devices are loaded lazily per Brand via a DeviceFetcher, so a run that only touches a
single brand (e.g. all rows are Samsung Galaxy) only pays for one brand's device fetch.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

from utils import collapse_ws, load_json, save_json


# ---- Types ---------------------------------------------------------------


class WebSearcher(Protocol):
    """Pluggable search backend. Returns ranked candidates."""

    def search(self, query: str) -> list["SearchResult"]: ...


class DeviceFetcher(Protocol):
    """Pluggable device-list fetcher. Given a Brand name, returns its Devices."""

    def fetch(self, brand_name: str) -> list[str]: ...


@dataclass
class SearchResult:
    candidate: str
    source_url: str | None = None
    snippet: str | None = None
    confidence: float = 0.0


@dataclass
class BrandEntry:
    name: str

    def norm(self) -> str:
        return collapse_ws(self.name).lower()


@dataclass
class CrmCatalog:
    """In-memory view of the CRM Brand list + lazy-loaded per-brand device lists.

    Brand list is loaded once eagerly. Device lists are loaded on demand the first time
    a brand is touched and memoized for the rest of the run.
    """

    brands: list[BrandEntry]
    devices_by_brand_norm: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_names(cls, brand_names: list[str]) -> "CrmCatalog":
        seen: set[str] = set()
        brands: list[BrandEntry] = []
        for raw in brand_names:
            name = (raw or "").strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            brands.append(BrandEntry(name=name))
        return cls(brands=brands)

    def brand_names(self) -> list[str]:
        return [b.name for b in self.brands]

    def find_brand_by_name(self, name: str) -> BrandEntry | None:
        target = collapse_ws(name).lower()
        if not target:
            return None
        for b in self.brands:
            if b.norm() == target:
                return b
        return None

    def find_brand_prefix(self, candidate: str) -> BrandEntry | None:
        """Find the longest Brand name that is a whole-word prefix of `candidate`."""
        cand_norm = collapse_ws(candidate).lower()
        if not cand_norm:
            return None
        best: BrandEntry | None = None
        best_len = 0
        for b in self.brands:
            bn = b.norm()
            if not bn:
                continue
            if cand_norm == bn or cand_norm.startswith(bn + " "):
                if len(bn) > best_len:
                    best = b
                    best_len = len(bn)
        return best

    def get_or_fetch_devices(self, brand_name: str, fetcher: DeviceFetcher) -> list[str]:
        key = collapse_ws(brand_name).lower()
        cached = self.devices_by_brand_norm.get(key)
        if cached is not None:
            return cached
        devices = fetcher.fetch(brand_name) or []
        self.devices_by_brand_norm[key] = devices
        return devices

    def preload_devices(self, brand_name: str, devices: list[str]) -> None:
        """Inject a device list (e.g. from the on-disk cache) without fetching."""
        key = collapse_ws(brand_name).lower()
        self.devices_by_brand_norm[key] = list(devices)


def find_device_in_list(devices: list[str], target: str) -> str | None:
    """Match a device name within a list, returning the canonical CRM string or None."""
    if not target:
        return None
    target_norm = collapse_ws(target).lower()
    for d in devices:
        if collapse_ws(d).lower() == target_norm:
            return d
    return None


@dataclass
class ResolutionOutcome:
    row: int
    original_manufacturer: str | None
    original_model_number: str | None
    resolved_manufacturer: str | None
    resolved_model_number: str | None
    method: str  # "already_correct" | "brand_device_direct" | "sku_cache" | "web_search" | "unresolved"
    search_query: str | None = None
    search_candidate: str | None = None
    search_source_url: str | None = None
    search_snippet: str | None = None
    error: str | None = None


@dataclass
class ResolutionReport:
    outcomes: list[ResolutionOutcome] = field(default_factory=list)

    @property
    def unresolved(self) -> list[ResolutionOutcome]:
        return [o for o in self.outcomes if o.method == "unresolved"]

    @property
    def resolved_via_search(self) -> list[ResolutionOutcome]:
        return [o for o in self.outcomes if o.method == "web_search"]


# ---- Cache ---------------------------------------------------------------


def cache_key(manufacturer: str, model_number: str) -> str:
    return collapse_ws(f"{manufacturer or ''}||{model_number or ''}").upper()


def load_sku_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"lookups": {}}
    data = load_json(path)
    data.setdefault("lookups", {})
    return data


def save_sku_cache(path: Path, cache: dict[str, Any]) -> None:
    save_json(path, cache)


# ---- Main resolver -------------------------------------------------------


def resolve_rows(
    rows: list[dict[str, Any]],
    rows_needing_resolution: list[int],
    *,
    catalog: CrmCatalog,
    device_fetcher: DeviceFetcher,
    sku_cache: dict[str, Any],
    web_searcher: WebSearcher,
    search_query_template: str,
    min_confidence: float,
    on_log: Callable[[str], None] | None = None,
) -> ResolutionReport:
    """Resolve each row's (Manufacturer, Model Number) against the catalog.

    `rows` is mutated: cells are rewritten when a row resolves to a different (Brand, Device)
    than the original input.
    """
    report = ResolutionReport()
    log = on_log or (lambda msg: None)

    for idx, row in enumerate(rows, start=1):
        mfr = _str(row.get("Manufacturer"))
        model = _str(row.get("Model Number"))

        # Step 1 — direct (Brand, Device) match
        outcome = _try_direct_match(idx, mfr, model, row, catalog, device_fetcher)
        if outcome is not None:
            report.outcomes.append(outcome)
            continue

        # Step 2 — SKU cache (validated against live catalog)
        outcome = _try_sku_cache(idx, mfr, model, row, sku_cache, catalog, device_fetcher)
        if outcome is not None:
            log(f"Row {idx}: resolved via SKU cache -> {outcome.resolved_manufacturer} / {outcome.resolved_model_number}")
            report.outcomes.append(outcome)
            continue

        # Step 3 — web search + reconcile
        query = search_query_template.format(manufacturer=mfr, model_number=model)
        log(f"Row {idx}: searching {query!r}")
        try:
            results = web_searcher.search(query) or []
        except Exception as exc:
            report.outcomes.append(
                _unresolved(idx, mfr, model, query=query, error=f"search_exception: {exc}")
            )
            continue

        if not results:
            report.outcomes.append(
                _unresolved(idx, mfr, model, query=query, error="search_returned_no_results")
            )
            continue

        chosen: ResolutionOutcome | None = None
        last_error: str | None = None
        last_candidate: SearchResult | None = None
        for result in sorted(results, key=lambda r: r.confidence, reverse=True):
            if result.confidence < min_confidence:
                continue
            last_candidate = result
            attempt = _try_search_candidate(
                idx, mfr, model, row,
                result=result,
                catalog=catalog,
                device_fetcher=device_fetcher,
                query=query,
            )
            if attempt is not None and attempt.method == "web_search":
                chosen = attempt
                sku_cache.setdefault("lookups", {})[cache_key(mfr, model)] = {
                    "manufacturer": attempt.resolved_manufacturer,
                    "model_number": attempt.resolved_model_number,
                    "search_candidate": result.candidate,
                    "search_source_url": result.source_url,
                    "confidence": result.confidence,
                }
                break
            if attempt is not None:
                last_error = attempt.error

        if chosen is None:
            report.outcomes.append(
                _unresolved(
                    idx, mfr, model,
                    query=query,
                    candidate=last_candidate.candidate if last_candidate else (results[0].candidate if results else None),
                    source_url=last_candidate.source_url if last_candidate else (results[0].source_url if results else None),
                    error=last_error or "no_high_confidence_match",
                )
            )
        else:
            report.outcomes.append(chosen)

    return report


# ---- Resolution strategies ------------------------------------------------


def _try_direct_match(
    idx: int, mfr: str, model: str, row: dict[str, Any],
    catalog: CrmCatalog, device_fetcher: DeviceFetcher,
) -> ResolutionOutcome | None:
    """Direct check: (CSV Manufacturer, CSV Model Number) maps to (CRM Brand, CRM Device).

    Returns None if no direct match. Returns an outcome with method=already_correct (cells
    were exact) or brand_device_direct (cells were normalized to CRM casing) on success.
    """
    if not mfr:
        return None
    brand = catalog.find_brand_by_name(mfr)
    if brand is None:
        return None
    devices = catalog.get_or_fetch_devices(brand.name, device_fetcher)
    device_match = find_device_in_list(devices, model)
    if device_match is None:
        return None
    if mfr == brand.name and model == device_match:
        return ResolutionOutcome(
            row=idx,
            original_manufacturer=mfr or None,
            original_model_number=model or None,
            resolved_manufacturer=brand.name,
            resolved_model_number=device_match,
            method="already_correct",
        )
    row["Manufacturer"] = brand.name
    row["Model Number"] = device_match
    return ResolutionOutcome(
        row=idx,
        original_manufacturer=mfr or None,
        original_model_number=model or None,
        resolved_manufacturer=brand.name,
        resolved_model_number=device_match,
        method="brand_device_direct",
    )


def _try_sku_cache(
    idx: int, mfr: str, model: str, row: dict[str, Any],
    sku_cache: dict[str, Any], catalog: CrmCatalog, device_fetcher: DeviceFetcher,
) -> ResolutionOutcome | None:
    cached = sku_cache.get("lookups", {}).get(cache_key(mfr, model))
    if not cached:
        return None
    cached_brand_name = cached.get("manufacturer") or ""
    cached_device_name = cached.get("model_number") or ""
    brand = catalog.find_brand_by_name(cached_brand_name)
    if brand is None:
        return None
    devices = catalog.get_or_fetch_devices(brand.name, device_fetcher)
    device_match = find_device_in_list(devices, cached_device_name)
    if device_match is None:
        return None
    row["Manufacturer"] = brand.name
    row["Model Number"] = device_match
    return ResolutionOutcome(
        row=idx,
        original_manufacturer=mfr or None,
        original_model_number=model or None,
        resolved_manufacturer=brand.name,
        resolved_model_number=device_match,
        method="sku_cache",
    )


def _try_search_candidate(
    idx: int, mfr: str, model: str, row: dict[str, Any],
    *, result: SearchResult, catalog: CrmCatalog, device_fetcher: DeviceFetcher, query: str,
) -> ResolutionOutcome | None:
    """Attempt to reconcile a single search candidate.

    Returns an outcome with method=web_search on success, or method=unresolved with an
    error explaining why this candidate didn't fit so the caller can move on to the next.
    """
    candidate = collapse_ws(result.candidate)
    if not candidate:
        return _unresolved(idx, mfr, model, query=query, candidate=result.candidate,
                           source_url=result.source_url, error="empty_search_candidate")

    brand = catalog.find_brand_prefix(candidate)
    used_fallback_brand = False
    if brand is None and mfr:
        brand = catalog.find_brand_by_name(mfr)
        used_fallback_brand = brand is not None

    if brand is None:
        return _unresolved(
            idx, mfr, model,
            query=query, candidate=result.candidate, source_url=result.source_url,
            error=f"no_brand_matches_candidate: {candidate!r}",
        )

    device_portion = _strip_brand_prefix(candidate, brand.name)
    if not device_portion and used_fallback_brand:
        device_portion = candidate
    if not device_portion:
        return _unresolved(
            idx, mfr, model,
            query=query, candidate=result.candidate, source_url=result.source_url,
            error=f"no_device_portion_after_brand_stripped (brand={brand.name!r})",
        )

    devices = catalog.get_or_fetch_devices(brand.name, device_fetcher)
    device_match = find_device_in_list(devices, device_portion)
    if device_match is None:
        return _unresolved(
            idx, mfr, model,
            query=query, candidate=result.candidate, source_url=result.source_url,
            error=f"device_not_in_brand: {device_portion!r} not under brand {brand.name!r}",
        )

    row["Manufacturer"] = brand.name
    row["Model Number"] = device_match
    return ResolutionOutcome(
        row=idx,
        original_manufacturer=mfr or None,
        original_model_number=model or None,
        resolved_manufacturer=brand.name,
        resolved_model_number=device_match,
        method="web_search",
        search_query=query,
        search_candidate=result.candidate,
        search_source_url=result.source_url,
        search_snippet=result.snippet,
    )


# ---- Helpers ------------------------------------------------------------


def _strip_brand_prefix(candidate: str, brand_name: str) -> str:
    cand_norm = candidate.lower()
    brand_norm = brand_name.lower()
    if cand_norm == brand_norm:
        return ""
    if cand_norm.startswith(brand_norm + " "):
        return candidate[len(brand_name) + 1:].strip()
    return ""


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _unresolved(
    idx: int, mfr: str, model: str, *,
    query: str | None = None, candidate: str | None = None, source_url: str | None = None,
    error: str | None = None,
) -> ResolutionOutcome:
    return ResolutionOutcome(
        row=idx,
        original_manufacturer=mfr or None,
        original_model_number=model or None,
        resolved_manufacturer=None,
        resolved_model_number=None,
        method="unresolved",
        search_query=query,
        search_candidate=candidate,
        search_source_url=source_url,
        error=error,
    )


# ---- Stubs ---------------------------------------------------------------


class StubSearcher:
    """Always returns nothing — keeps the module importable without a network dep."""

    def search(self, query: str) -> list[SearchResult]:
        return []


class NoopDeviceFetcher:
    """Returns an empty device list for any brand — for dry-runs or unit tests."""

    def fetch(self, brand_name: str) -> list[str]:
        return []


if __name__ == "__main__":  # pragma: no cover — manual smoke test
    import json
    import sys

    if len(sys.argv) != 2:
        print("usage: resolve_model_names.py <brand_menu_cache.json>")
        sys.exit(2)
    cache = load_json(Path(sys.argv[1]))
    catalog = CrmCatalog.from_names(cache.get("brands", []))
    print(json.dumps({
        "brand_count": len(catalog.brands),
        "first_10_brands": catalog.brand_names()[:10],
        "preloaded_device_brands": list((cache.get("devices_by_brand") or {}).keys()),
    }, indent=2))
