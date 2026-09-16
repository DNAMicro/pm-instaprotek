"""Ownership guard — no edit/save/delete may touch a record we did not create.

The 2026-09-16 incident: plan creation failed, the driver's grid-search recovery
returned a positive row count against a search box that does not filter, so it
opened a REAL production plan and its teardown deleted it. Never again: prove
ownership from the open record's own text before any write."""
TAG = "RegressionTest0916"
VERIFY_TAGS = ("RegressionTest0916", "RegTest20260916", "VerifyTest0916", "VerifyTwo0916")

class NotOurs(Exception):
    """Raised when a write was attempted on a record we did not create."""

def record_text(pg):
    return pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')
        ||document.querySelector('.advancedFullDialog')||document.querySelector('.md-dialog');
      return d?d.innerText:'';}""")

def is_ours(pg):
    t = record_text(pg) or ""
    return any(tag in t for tag in VERIFY_TAGS)

def assert_ours(pg, what="write"):
    """Abort unless the OPEN record is demonstrably one this run created."""
    t = record_text(pg) or ""
    if not t.strip():
        raise NotOurs(f"{what} refused: no record shell is open (cannot prove ownership)")
    if not any(tag in t for tag in VERIFY_TAGS):
        raise NotOurs(f"{what} refused: open record is NOT ours — header: {t[:150].strip()!r}")
    return True

def safe_delete(pg, what="record"):
    """Delete only after proving ownership. Returns (ok, message)."""
    try:
        assert_ours(pg, f"delete of {what}")
    except NotOurs as e:
        return (False, str(e))
    n = pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')
        ||document.querySelector('.advancedFullDialog');if(!d)return 0;
      const b=[...d.querySelectorAll('button')].find(x=>/delete/i.test(x.textContent));
      if(b){b.click();return 1;}return 0;}""")
    return (bool(n), "delete clicked" if n else "no delete control found")
