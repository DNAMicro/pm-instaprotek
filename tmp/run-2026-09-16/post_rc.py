import json, urllib.request
cfg=json.load(open('/home/farsheed/pm-instaprotek/.claude/skills/instaprotek-enterprise-registration/config/settings.json'))
url=cfg['webhook']['url']
text = """**⚠️ Instaprotek Regression PROD-2026-09-16 — HALTED · Production data loss**

A regression run against `crm.instaprotek.com` **deleted a live production plan**: `2 - Years Warranty Replacement` (id `d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a`, USD 9.16, United States, 2-year). Deleted today **11:53 AM MST**. Two Save actions and a test note were also written to it beforehand.

**Cause — test harness, not a product defect.** The test plan failed to create, so the driver fell back to "search the grid for our tag, open the first match". The Plans grid search does not filter, so it opened a **real** plan and its teardown deleted it.

**Not recoverable in-portal** — hard delete, absent from CSV export, Timeline logs only name + amount. **Needs a DB restore of that row from a backup before 2026-09-16 18:53 UTC, preserving the original id.**

**Status:** run halted at 372/979 scenarios. Nothing is touching Production. Harness fixed — every edit/delete now proves record ownership first (verified blocking a real record); the faulty recovery path is removed.

Details: `Insta-testing/incidents/2026-09-16-production-plan-deleted.md` (commit `eeeed99`)"""
payload=json.dumps({"title":"⚠️ Instaprotek Regression PROD-2026-09-16 — Production data loss","text":text}).encode()
req=urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("RingCentral POST status:", r.status)
        print("response:", r.read()[:200].decode(errors="replace"))
except Exception as e:
    print("POST failed:", type(e).__name__, str(e)[:200])
