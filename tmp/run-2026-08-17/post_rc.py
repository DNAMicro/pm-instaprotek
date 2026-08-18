import json, urllib.request
cfg=json.load(open('/home/farsheed/pm-instaprotek/.claude/skills/instaprotek-enterprise-registration/config/settings.json'))
url=cfg['webhook']['url']
PAGE="https://dnamicro.atlassian.net/wiki/spaces/IE/pages/863535121"
text = """**Instaprotek Regression Run — NULLNET-2026-08-17 — COMPLETE**

**Environment:** `crm.nullnet.instaprotek.com` (as directed by PM — *not* QA). Note this host carries **live production data** (1.26M registrations, 123k claims, counters moving during the run), so scenarios that would have created/altered real customer records or emailed a real customer were deliberately not executed and are logged as Blocked with reasons.

**Results:** 979 scenarios — **774 Pass · 20 Fail · 28 Blocked · 157 N/A (out of scope)**
**Pass rate: 97.5%** of the 794 executed.

**Open defects:** 0 Critical · **2 High** · 5 Medium · 2 Low — 9 bugs filed in INSTA (unassigned, label `regression`, sprint 5590):
• INSTA-1401 (High) — Languages settings filter crashes the whole page to a blank screen, on every filter column
• INSTA-1402 (High) — company delete + plan removal both fail with HTTP 400 and show no error
• INSTA-1403 — company Status selector won't apply Inactive
• INSTA-1404 — claim Repair Receipt "covered amount" rejects all input
• INSTA-1405 — claim wizard required Notes field not enforced
• INSTA-1406 — Add Devices step-2 search doesn't filter
• INSTA-1407 — Product Category records write no timeline entries
• INSTA-1408 — Repair Network filter returns no values
• INSTA-1409 — New User country list missing Japan/Mexico/Spain, extra Puerto Rico

A further 8 findings are logged as **deviations for PM confirmation** (fields/tabs the test cases expect that don't exist on this build) rather than filed as bugs.

**Recommendation: NO-GO pending the two High defects.** Pass rate clears the 95% gate and the portal is broadly healthy, but INSTA-1401 and INSTA-1402 are open. If the business accepts them as known issues this becomes a conditional GO — PM call.

**Needs manual cleanup:** test company `RegressionTest0817` could not be removed (delete returns 400, status won't change) — see INSTA-1402/1403. Everything else created for the run was deleted.

**Full report:** """ + PAGE

payload=json.dumps({"title":"Instaprotek Regression — NULLNET-2026-08-17","text":text}).encode()
req=urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("RingCentral POST status:", r.status)
        print("response:", r.read()[:200].decode(errors="replace"))
except Exception as e:
    print("POST failed:", type(e).__name__, str(e)[:200])
