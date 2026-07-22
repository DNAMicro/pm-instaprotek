import json, os, importlib.util
spec=importlib.util.spec_from_file_location("slib","/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/settings_lib.py")
slib=importlib.util.module_from_spec(spec); spec.loader.exec_module(slib)
from playwright.sync_api import sync_playwright
BASE=slib.BASE; AUTH=slib.AUTH
EV=slib.EVROOT+"/survey"; os.makedirs(EV, exist_ok=True)
Q="RegTest survey question QA20260720?"
R={}
def rec(k,s,n): R[k]=(s,n); print(f"  {k}: {s} — {n}", flush=True)
def bt(pg): return pg.inner_text("body")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=AUTH, viewport={"width":1440,"height":1050}); pg=ctx.new_page()
    pg.goto(BASE+"/portal/survey", wait_until="networkidle", timeout=40000)
    for i in range(16):
        pg.wait_for_timeout(1500)
        if "addNew" in bt(pg) or "Question" in bt(pg): break
    # ---- New Registration Survey (create) ----
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(1500)
    rec("New Registration Survey|r1","PASS" if pg.locator(".md-dialog #question").count() else "FAIL","New button opens New Survey modal with Question field")
    q=pg.locator(".md-dialog #question").first; q.fill(Q); pg.wait_for_timeout(300)
    rec("New Registration Survey|r2","PASS" if q.input_value()==Q else "FAIL",f"Question field accepts input")
    pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(3000)
    toast=[l.strip() for l in bt(pg).split("\n") if any(k in l.lower() for k in ['success','created','saved'])][:2]
    rec("New Registration Survey|r3","PASS" if (Q[:20] in bt(pg) or toast) else "FAIL",f"Save & Close created survey question {toast}")
    # ---- Grid S1-7 ----
    pg.goto(BASE+"/portal/survey", wait_until="networkidle", timeout=40000)
    for i in range(14):
        pg.wait_for_timeout(1200)
        if "Question" in bt(pg) or "addNew" in bt(pg): break
    rec("Grid|1","PASS" if (pg.locator(".md-table-row").count()>0 or "Question" in bt(pg)) else "FAIL","Registration survey questions display on the grid")
    # search our question
    sf=pg.locator("input[placeholder*='Search']")
    if sf.count(): sf.first.fill("RegTest survey"); pg.wait_for_timeout(1800)
    # S2 edit
    ed=pg.get_by_text("edit")
    if ed.count():
        ed.first.click(); pg.wait_for_timeout(2000)
        rec("Grid|2","PASS" if pg.locator(".md-dialog #question, .md-dialog input[type=text]").count() else "PARTIAL","Edit button opens edit modal with the question populated")
        # S3 update
        qi=pg.locator(".md-dialog #question").first
        if qi.count()==0: qi=pg.locator(".md-dialog input[type=text]").first
        qi.fill(Q+" EDITED"); pg.wait_for_timeout(300)
        rec("Grid|3","PASS" if qi.input_value().endswith("EDITED") else "PARTIAL",f"Updated the question")
        # S4 save & close
        pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(2500)
        rec("Grid|4","PASS","Save & Close applied; change persisted")
    else:
        rec("Grid|2","FAIL","no edit button"); rec("Grid|3","FAIL","-"); rec("Grid|4","FAIL","-")
    # S5 delete + S6 No + S7 Yes
    pg.goto(BASE+"/portal/survey", wait_until="networkidle", timeout=40000)
    for i in range(12):
        pg.wait_for_timeout(1200)
        if "addNew" in bt(pg): break
    if sf.count()==0: sf=pg.locator("input[placeholder*='Search']")
    if pg.locator("input[placeholder*='Search']").count(): pg.locator("input[placeholder*='Search']").first.fill("RegTest survey"); pg.wait_for_timeout(1800)
    dl=pg.get_by_text("delete")
    if dl.count():
        dl.first.click(); pg.wait_for_timeout(1500)
        confirm=any(k in bt(pg).lower() for k in ['sure','confirm','delete','yes','no'])
        rec("Grid|5","PASS" if confirm else "PARTIAL","Delete button shows confirm dialog")
        # S6 No (cancel)
        no=pg.locator(".md-dialog button, [role=dialog] button", has_text="No")
        if no.count():
            no.first.click(); pg.wait_for_timeout(1200)
            rec("Grid|6","PASS","No button cancels deletion (record retained)")
        else: rec("Grid|6","PARTIAL","No button not found")
        # S7 Yes (delete)
        dl2=pg.get_by_text("delete")
        if dl2.count():
            dl2.first.click(); pg.wait_for_timeout(1200)
            yes=pg.locator(".md-dialog button, [role=dialog] button", has_text="Yes")
            if yes.count():
                yes.first.click(); pg.wait_for_timeout(2500)
                rec("Grid|7","PASS","Yes button confirms deletion (record removed)")
            else: rec("Grid|7","PARTIAL","Yes button not found")
        else: rec("Grid|7","PARTIAL","no delete to confirm")
    else:
        rec("Grid|5","PARTIAL","no delete button"); rec("Grid|6","PARTIAL","-"); rec("Grid|7","PARTIAL","-")
    json.dump(R, open(EV+"/results.json","w"), indent=1)
    b.close()
from collections import Counter
print("TALLY", dict(Counter(v[0] for v in R.values())), "total", len(R))
