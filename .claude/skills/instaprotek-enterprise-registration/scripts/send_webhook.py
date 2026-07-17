"""Post run summaries to the RingCentral inbound webhook.

RingCentral inbound webhooks accept a JSON body with `title` and `text` (markdown). They also
accept richer payloads with `attachments` (Card v2). We use the simple title+text form because
it works reliably across legacy and current webhook generations.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import requests


@dataclass
class SuccessPayload:
    po_number: str | None
    company: str
    plan: str | None
    pin_count: int | None
    end_user: str | None
    transaction_date: str | None
    effective_date: str | None
    auto_fixed_rows: int
    flagged_rows: int
    processed_folder: str
    run_timestamp: str
    crm_url: str | None = None


@dataclass
class FailurePayload:
    po_number: str | None
    stage: str  # e.g. "discover_files", "validate", "resolve_models", "playwright_login"
    reason: str
    details: dict[str, Any] = field(default_factory=dict)
    failed_folder: str | None = None
    run_timestamp: str = ""


# ---- Formatters ----------------------------------------------------------


def format_success_message(p: SuccessPayload) -> dict[str, str]:
    title = f"InstaProtek registration submitted — PO {p.po_number or 'UNKNOWN'}"
    lines = [
        f"**Plan:** {p.plan or '—'}",
        f"**Pins:** {p.pin_count if p.pin_count is not None else '—'}",
        f"**End user:** {p.end_user or '—'}",
        f"**Transaction date:** {p.transaction_date or '—'}",
        f"**Effective date:** {p.effective_date or '—'}",
        f"**Auto-corrected rows:** {p.auto_fixed_rows}",
        f"**Flagged rows:** {p.flagged_rows}",
        f"**Run folder:** `{p.processed_folder}`",
        f"**Run timestamp (UTC):** {p.run_timestamp}",
    ]
    return {"title": title, "text": "\n".join(lines)}


def format_failure_message(p: FailurePayload) -> dict[str, str]:
    title = f"InstaProtek registration FAILED — PO {p.po_number or 'UNKNOWN'}"
    lines = [
        f"**Stage:** {p.stage}",
        f"**Reason:** {p.reason}",
    ]
    if p.details:
        details_json = json.dumps(p.details, indent=2, default=str)
        if len(details_json) > 1500:
            details_json = details_json[:1500] + "\n…(truncated)"
        lines.append("**Details:**")
        lines.append("```")
        lines.append(details_json)
        lines.append("```")
    if p.failed_folder:
        lines.append(f"**Failure folder:** `{p.failed_folder}`")
    if p.run_timestamp:
        lines.append(f"**Run timestamp (UTC):** {p.run_timestamp}")
    return {"title": title, "text": "\n".join(lines)}


# ---- Poster --------------------------------------------------------------


def post_webhook(
    url: str,
    body: dict[str, Any],
    *,
    timeout_seconds: int = 15,
    save_to: Path | None = None,
) -> dict[str, Any]:
    response_meta: dict[str, Any] = {"url": url, "request_body": body}
    try:
        r = requests.post(url, json=body, timeout=timeout_seconds)
        response_meta["status_code"] = r.status_code
        response_meta["response_text"] = r.text[:2000]
        response_meta["ok"] = r.ok
    except Exception as exc:
        response_meta["status_code"] = None
        response_meta["error"] = str(exc)
        response_meta["ok"] = False

    if save_to is not None:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        with save_to.open("w", encoding="utf-8") as f:
            json.dump(response_meta, f, indent=2, default=str)
    return response_meta


def post_success(url: str, payload: SuccessPayload, *, save_to: Path | None = None, timeout_seconds: int = 15) -> dict[str, Any]:
    body = format_success_message(payload)
    return post_webhook(url, body, timeout_seconds=timeout_seconds, save_to=save_to)


def post_failure(url: str, payload: FailurePayload, *, save_to: Path | None = None, timeout_seconds: int = 30) -> dict[str, Any]:
    body = format_failure_message(payload)
    # Failure payloads get a longer timeout so we don't lose alerts on slow links.
    return post_webhook(url, body, timeout_seconds=timeout_seconds, save_to=save_to)


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        print("usage: send_webhook.py <webhook-url> [--failure]")
        sys.exit(2)
    url = sys.argv[1]
    is_failure = "--failure" in sys.argv[2:]
    if is_failure:
        payload = FailurePayload(
            po_number="DRYRUN",
            stage="manual_test",
            reason="dry run from cli",
            details={"note": "this is a test"},
            run_timestamp="dry-run",
        )
        print(json.dumps(post_failure(url, payload), indent=2, default=str))
    else:
        payload = SuccessPayload(
            po_number="DRYRUN",
            company="Demo Company",
            plan="Test Plan",
            pin_count=0,
            end_user="Test User",
            transaction_date="2026-01-01",
            effective_date="2026-01-01",
            auto_fixed_rows=0,
            flagged_rows=0,
            processed_folder="dry-run",
            run_timestamp="dry-run",
        )
        print(json.dumps(post_success(url, payload), indent=2, default=str))
