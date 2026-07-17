"""Extract structured fields from an InstaProtek Purchase Order PDF.

The CSG PO uses a bordered-table layout. pdfplumber's `extract_tables()` cleanly returns the
ITEMS ON ORDER block, including the duplicated plan description spanning the Item and
Description columns. Header-less data (the PO number in the upper right, the Order Date row
below the Ship Date/Terms/Sales Order/Order Date header) is recovered via word coordinates.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber

from utils import collapse_ws, parse_date_flexible


@dataclass
class EndUser:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


@dataclass
class PurchaseOrder:
    po_number: str | None = None
    order_date: datetime | None = None
    plan_description: str | None = None
    quantity: int | None = None
    rate: float | None = None
    total: float | None = None
    end_user: EndUser = field(default_factory=EndUser)
    source_filename: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if isinstance(self.order_date, datetime):
            d["order_date"] = self.order_date.strftime("%Y-%m-%d")
        return d


_DATE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
_MONEY_RE = re.compile(r"\$?([\d,]+\.\d{2})")
_INT_RE = re.compile(r"^\d{1,6}$")
_EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
_PO_NUM_CANDIDATE_RE = re.compile(r"^[A-Z0-9][A-Z0-9\-]{2,}$", re.IGNORECASE)


def parse_purchase_order(pdf_path: Path) -> PurchaseOrder:
    po = PurchaseOrder(source_filename=pdf_path.name)

    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        tables = page.extract_tables()

        po.po_number = _extract_po_number(words)
        po.order_date = _extract_order_date(words)

        items_table = _find_items_table(tables)
        if items_table is not None:
            plan_description, qty, rate, total = _parse_items_table(items_table)
            po.plan_description = plan_description
            po.quantity = qty
            po.rate = rate
            po.total = total
            po.end_user = _parse_end_user_from_items_table(items_table)
        else:
            # Fallback: try a full-text regex if the table parser missed it.
            text = page.extract_text() or ""
            po.end_user = _parse_end_user_from_text(text)

    return po


# ---- PO number (upper-right region, beneath "Purchase Order #") ----------


def _extract_po_number(words: list[dict]) -> str | None:
    """Find the PO number by locating the 'Purchase Order #' label and then the next standalone
    alphanumeric token in the upper-right column.
    """
    # Locate the right-most "#" that follows "Purchase" "Order" on the same line in the upper region.
    header_top = None
    header_x_max = None
    for i, w in enumerate(words):
        if w.get("text") == "#":
            # Look backwards for "Order" and "Purchase" nearby on the same line
            same_line = [
                x for x in words
                if abs(x.get("top", 0) - w.get("top", 0)) < 4 and x.get("x0", 0) < w.get("x0", 0)
            ]
            texts = [x.get("text", "") for x in same_line[-3:]]
            if "Purchase" in texts and "Order" in texts:
                header_top = w.get("top", 0)
                header_x_max = w.get("x1", 0)
                break
    if header_top is None:
        return None

    # Candidate PO numbers: any word in the right column (x0 in the right half of the page)
    # whose top is within ~120pt below the header. Must look alphanumeric.
    page_right_threshold = (header_x_max or 0) - 200  # generous right-column boundary
    candidates: list[tuple[float, str]] = []
    for w in words:
        wy = w.get("top", 0)
        wx = w.get("x0", 0)
        text = (w.get("text") or "").strip()
        if not text:
            continue
        if wy <= header_top + 4:  # must be below the header
            continue
        if wy - header_top > 120:
            continue
        if wx < page_right_threshold:  # must be in the right column
            continue
        if not _PO_NUM_CANDIDATE_RE.match(text):
            continue
        # Skip pure date-looking tokens
        if _DATE_RE.match(text):
            continue
        candidates.append((wy, text))

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[0][1]


# ---- Order Date (below the Ship Date/Terms/Sales Order/Order Date header) ----


def _extract_order_date(words: list[dict]) -> datetime | None:
    """Find the 'Order Date' header row and return the date below the 'Order Date' column."""
    # Locate "Order" + "Date" on the same line (header row).
    header_top = None
    order_x_center = None
    for w in words:
        if (w.get("text") or "").lower() != "order":
            continue
        for w2 in words:
            if (w2.get("text") or "").lower() != "date":
                continue
            if abs(w2.get("top", 0) - w.get("top", 0)) < 4 and 0 < (w2.get("x0", 0) - w.get("x1", 0)) < 40:
                header_top = w.get("top", 0)
                order_x_center = (w.get("x0", 0) + w2.get("x1", 0)) / 2
                break
        if header_top is not None:
            break

    if header_top is None or order_x_center is None:
        return _fallback_first_date(words)

    candidates: list[tuple[float, float, datetime]] = []
    for w in words:
        text = (w.get("text") or "").strip()
        if not _DATE_RE.fullmatch(text):
            continue
        wy = w.get("top", 0)
        if wy <= header_top + 4 or wy - header_top > 40:
            continue
        wx = (w.get("x0", 0) + w.get("x1", 0)) / 2
        dt = parse_date_flexible(text)
        if dt is None:
            continue
        candidates.append((abs(wx - order_x_center), wy, dt))
    if candidates:
        candidates.sort()
        return candidates[0][2]
    return _fallback_first_date(words)


def _fallback_first_date(words: list[dict]) -> datetime | None:
    dates: list[datetime] = []
    for w in words:
        text = (w.get("text") or "").strip()
        if _DATE_RE.fullmatch(text):
            dt = parse_date_flexible(text)
            if dt is not None:
                dates.append(dt)
    if not dates:
        return None
    return max(dates)


# ---- Items table ---------------------------------------------------------


def _find_items_table(tables: list[list[list[Any]]]) -> list[list[Any]] | None:
    for table in tables:
        # Look for a row whose lowercase joined value contains "items on order" or
        # whose header row is ["Item", "Description", "Quantity", "Rate", "Amount"].
        if not table or not any(table):
            continue
        flat = " ".join(str(cell or "").lower() for row in table for cell in row)
        if "items on order" in flat:
            return table
        if any(
            row
            and len(row) >= 5
            and (row[0] or "").strip().lower() == "item"
            and (row[1] or "").strip().lower() == "description"
            for row in table
        ):
            return table
    return None


def _parse_items_table(table: list[list[Any]]):
    """Find the line-item row and return (plan_description, qty, rate, total)."""
    plan_description = None
    qty = None
    rate = None
    total = None

    # The data row is the one whose Quantity column parses as an int and whose Item/Description
    # columns are populated.
    for row in table:
        if not row or len(row) < 5:
            continue
        item_cell = (row[0] or "").strip()
        desc_cell = (row[1] or "").strip()
        qty_cell = (row[2] or "").strip() if row[2] is not None else ""
        rate_cell = (row[3] or "").strip() if row[3] is not None else ""
        amount_cell = (row[4] or "").strip() if row[4] is not None else ""

        if not _INT_RE.match(qty_cell):
            continue

        qty = int(qty_cell)
        rate = _money(rate_cell)
        total = _money(amount_cell)
        # Plan description: prefer the Description column, fall back to Item column.
        desc = desc_cell or item_cell
        plan_description = _normalize_plan_text(desc)
        break

    return plan_description, qty, rate, total


def _money(cell: str) -> float | None:
    m = _MONEY_RE.search(cell)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _normalize_plan_text(text: str) -> str:
    """Cleaned: newline-separated lines joined with single spaces."""
    if not text:
        return ""
    return collapse_ws(text.replace("\n", " "))


# ---- End user ------------------------------------------------------------


def _parse_end_user_from_items_table(table: list[list[Any]]) -> EndUser:
    """The CSG PO emits a row whose Item column = 'EndUserInfo' and whose Description column
    contains the full block (Email, Phone, Address, multi-line name and address)."""
    for row in table:
        if not row:
            continue
        item_cell = (row[0] or "").strip().lower() if row[0] else ""
        if item_cell != "enduserinfo":
            continue
        block = (row[1] or "") if len(row) > 1 else ""
        return _parse_end_user_block(block)
    return EndUser()


def _parse_end_user_from_text(text: str) -> EndUser:
    idx = text.lower().find("enduserinfo")
    if idx == -1:
        return EndUser()
    return _parse_end_user_block(text[idx : idx + 600])


def _parse_end_user_block(block: str) -> EndUser:
    user = EndUser()
    if not block:
        return user

    # Email + phone anywhere in the block
    em = _EMAIL_RE.search(block)
    if em:
        user.email = em.group(0)
    ph = _PHONE_RE.search(block)
    if ph:
        user.phone = ph.group(0)

    # Address block sits after the literal "Address" line. Name is the first line after it,
    # remaining lines until "United States" / "USA" form the address.
    lines = [collapse_ws(line) for line in block.splitlines()]
    lines = [line for line in lines if line]

    try:
        addr_idx = next(i for i, line in enumerate(lines) if line.lower() == "address")
    except StopIteration:
        addr_idx = -1

    if addr_idx >= 0 and addr_idx + 1 < len(lines):
        user.name = lines[addr_idx + 1]
        addr_parts: list[str] = []
        for line in lines[addr_idx + 2 :]:
            low = line.lower()
            if low.startswith("total") or low.startswith("notes"):
                break
            addr_parts.append(line)
            if "united states" in low or low == "usa":
                break
        if addr_parts:
            user.address = ", ".join(addr_parts)

    return user


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys

    if len(sys.argv) != 2:
        print("usage: parse_po.py <path-to-po.pdf>")
        sys.exit(2)
    po = parse_purchase_order(Path(sys.argv[1]))
    print(json.dumps(po.to_dict(), indent=2, default=str))
