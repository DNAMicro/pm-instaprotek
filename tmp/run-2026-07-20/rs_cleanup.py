import json
from playwright.sync_api import sync_playwright
c=json.load(open("/home/farsheed/pm-instaprotek/credentials.json")); cfg=c[c["Env"]]
BASE=cfg["crm_base_url"].rstrip("/")
AUTH="/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/evidence/auth_state.json"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/evidence/repair-shops"
URL=open(EV+"/record_url.txt").read().strip()
def log(*a): print(*a, flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=AUTH, viewport={"width":1440,"height":1000}); pg=ctx.new_page()
    pg.goto(URL, wait_until="networkidle", timeout=40000)
    for i in range(14):
        pg.wait_for_timeout(1200)
        if "Branches" in pg.inner_text("body"): break
    # ---- delete all notes ----
    pg.get_by_text("Notes", exact=True).first.click(); pg.wait_for_timeout(1800)
    deleted=0
    for attempt in range(8):
        dels=pg.locator(".notes-grid button", has_text="delete")
        if dels.count()==0:
            dels=pg.get_by_text("delete")
        n=dels.count()
        if n==0: break
        try:
            dels.first.click(); pg.wait_for_timeout(1000)
            # confirm dialog?
            body=pg.inner_text("body")
            for lbl in ["Delete","Yes","Confirm","OK"]:
                cf=pg.locator(".md-dialog button, [role=dialog] button", has_text=lbl)
                if cf.count() and ("sure" in body.lower() or "delete" in body.lower()):
                    try: cf.first.click(); pg.wait_for_timeout(1200); break
                    except Exception: pass
            deleted+=1
            pg.wait_for_timeout(1200)
        except Exception as e:
            log("del err", str(e)[:60]); break
    log("notes delete attempts:", deleted)
    remaining_notes = pg.locator(".notes-grid").inner_text() if pg.locator(".notes-grid").count() else ""
    log("notes grid remaining text:", remaining_notes.replace("\n"," ")[:120])
    # ---- set shop status Inactive (soft-delete) ----
    pg.goto(URL, wait_until="networkidle", timeout=40000)
    for i in range(14):
        pg.wait_for_timeout(1200)
        if "Branches" in pg.inner_text("body"): break
    try:
        pg.locator("#status-toggle").first.click(); pg.wait_for_timeout(600)
        pg.locator(".md-list.md-layover-child [role=option]", has_text="Inactive").first.click(); pg.wait_for_timeout(600)
        # Save & Close
        sc=pg.locator("button", has_text="Save and Close").first
        if sc.count()==0: sc=pg.locator("button", has_text="Save & Close").first
        sc.click(); pg.wait_for_timeout(3000)
        body=pg.inner_text("body")
        log("status set Inactive; toast:", [l.strip() for l in body.split("\n") if any(k in l.lower() for k in ['success','saved','updated','inactive'])][:3])
    except Exception as e:
        log("status err", str(e)[:80])
    # verify
    pg.goto(BASE+"/portal/shop", wait_until="networkidle", timeout=40000)
    for i in range(14):
        pg.wait_for_timeout(1200)
        if "Filter Repair Shops" in pg.inner_text("body"): break
    pg.locator("#dnaTable2-searchField").fill("RegressionTest Shop"); pg.wait_for_timeout(2000)
    row=pg.inner_text("body")
    log("shop row after cleanup:", "RegressionTest ShopQA20260720" in row, "| Inactive shown:", "Inactive" in row)
    pg.screenshot(path=EV+"/cleanup_done.png", full_page=True)
    b.close()
log("CLEANUP DONE")
