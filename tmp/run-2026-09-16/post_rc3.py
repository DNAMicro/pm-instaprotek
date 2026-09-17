import json, urllib.request
cfg=json.load(open('/home/farsheed/pm-instaprotek/.claude/skills/instaprotek-enterprise-registration/config/settings.json'))
url=cfg['webhook']['url']
PAGE="https://dnamicro.atlassian.net/wiki/spaces/IE/pages/912654338"
text = """**Instaprotek Regression — PROD-2026-09-16 — COMPLETE**

**Environment:** Production `crm.instaprotek.com`, run 2026-09-16 to 09-17, account agentqa@dnamicro.com (Agent role).

**Results:** 979 scenarios — **209 Pass · 1 Fail · 250 Blocked · 519 N/A**
**99.5% of the 210 scenarios actually attempted passed.**

⚠️ **That 99.5% is not a release signal.** Only 210 of 979 were attempted. The updated Production scope bars create/edit/delete outside Registration and Claims, so 519 are N/A and 250 Blocked. This run confirms Production **renders and navigates** — it does not confirm that writes work. **No Go/No-go is offered; a release decision needs a full QA or Staging regression.**

**Open defects: 0 Critical · 1 High · 0 Medium · 0 Low**
• **INSTA-1401** (High, already open) — Settings > Languages filter collapses the whole page to an empty DOM. Previously seen only on nullnet, **now confirmed on Production**. Recorded as a comment on the existing ticket rather than filed as a duplicate. Narrowed: search, export and record-open all work on a fresh page, so the fix surface is just the filter's value-mapping path.

**No other bug was filed.** 16 of 17 first-pass failures were re-verified read-only and proved to be test-harness artifacts (slow page loads, a grid search that does not filter, section-name assumptions). Filing them unverified would have created 16 false tickets.

\U0001f6a8 **Outstanding action — Production data loss not yet resolved.** Plan `d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a` ("2 - Years Warranty Replacement") was deleted by the harness on 09-16 and still needs a **database restore** from a backup before 2026-09-16 18:53 UTC, preserving the original id. 289 registrations reference it; they display correctly but no new registration can be created against that plan.

**Blocked highlights:** Portal Registration (41) — creating the shared test registration needs a Pincode tied to real inventory, which was not fabricated on Production. Claim Reports record cases (41) — claim filing is app-only.

**Nothing was left behind on Production by the browse phase.** The harness now proves record ownership before any edit or delete.

**Full report (24 module pages, all 979 scenarios with expected vs actual):** """ + PAGE
payload=json.dumps({"title":"Instaprotek Regression — PROD-2026-09-16 — COMPLETE","text":text}).encode()
req=urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=30) as r:
    print("RingCentral POST status:", r.status, r.read()[:120].decode(errors="replace"))
