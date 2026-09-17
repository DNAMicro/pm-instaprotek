import json, urllib.request
cfg=json.load(open('/home/farsheed/pm-instaprotek/.claude/skills/instaprotek-enterprise-registration/config/settings.json'))
url=cfg['webhook']['url']
text = """**Deleted plan — details for re-entry**
Settings → Plans → New. Deleted 2026-09-16 11:53 AM MST. Old id `d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a` (a new record will get a new id).

**KNOWN — enter these:**
| Field | Value |
|---|---|
| Plan Name | `2 - Years Warranty Replacement` |
| Plan Code | *(leave empty)* |
| Region | `United States` |
| Coverage Amount | `9.16` (displays as USD 9.16) |
| Coverage Period | `2` |
| Terms (PDF) | filename starts `Terms and Cond...` — full name not captured |
| Profile image | the plan had an image uploaded |

**NOT RECOVERED — someone must supply these:**
SKU · Administrator · Underwriter · Support · Coverage Type · Coverage Cost Type · Coverage Type Amount · Channel

For reference, the similar `Lifetime Warranty Replacement` plans use: Administrator `InstaProtek`, Underwriter `InstaProtek`, Support `InstaProtek (Warranty)`, Coverage Type `Product Replacement`, Coverage Cost Type `Shipping & Handling`, SKU empty. **These are NOT confirmed for the deleted plan — do not copy them without checking.**

**Impact:** 289 existing registrations reference this plan. They still display the plan name correctly and are not visibly broken. But the plan is missing from the catalogue, so no new registration can be created against it.

**Preferred fix is a database restore** of the original row (backup before 2026-09-16 18:53 UTC, keeping the original id) — that recovers all fields and keeps the 289 registrations linked. Re-entering by hand creates a new id and still leaves 8 fields guessed.

Full record: `Insta-testing/incidents/2026-09-16-production-plan-deleted.md`"""
payload=json.dumps({"title":"Deleted plan — details for re-entry","text":text}).encode()
req=urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=30) as r:
    print("RingCentral POST status:", r.status, r.read()[:120].decode(errors="replace"))
