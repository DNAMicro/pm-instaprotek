"""READ-ONLY. Rewrite the grid request's `status` field in-flight and see what comes back."""
import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PLAN="2 - Years Warranty Replacement"
RESULTS={}
def run(status_value):
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
        captured={}
        def handler(route):
            req=route.request
            if req.method=="POST" and "/node/grid" in req.url:
                try:
                    body=json.loads(req.post_data or "{}")
                    if body.get("node")=="product_list":
                        body["status"]=status_value
                        route.continue_(post_data=json.dumps(body)); return
                except Exception: pass
            route.continue_()
        pg.route("**/node/grid", handler)
        def on_resp(r):
            if "/node/grid" in r.url and r.request.method=="POST":
                try:
                    t=r.text()
                    captured["status"]=r.status
                    captured["has_plan"]=PLAN in t
                    j=json.loads(t)
                    captured["total"]=j.get("total") or j.get("count") or (len(j.get("rows",[])) if isinstance(j.get("rows"),list) else None)
                    rows=j.get("rows") or j.get("data") or []
                    captured["names"]=[ (x.get("name") or x.get("plan_name") or "?") for x in rows][:60] if isinstance(rows,list) else []
                except Exception as e:
                    captured["err"]=str(e)[:80]
        pg.on("response", on_resp)
        pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
        for _ in range(40):
            pg.wait_for_timeout(3000)
            if captured: break
        pg.wait_for_timeout(6000)
        ui=pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'-';}""")
        body=pg.inner_text("body")
        RESULTS[status_value]={"api":captured,"ui_pagination":ui,"plan_on_page":PLAN in body}
        print(f"status={status_value!r:14s} -> api_total={captured.get('total')} has_plan={captured.get('has_plan')} ui={ui} plan_on_page={PLAN in body}", flush=True)
        if captured.get("has_plan") or PLAN in body:
            print("   *** DELETED PLAN FOUND ***", flush=True)
            for n in captured.get("names",[]):
                if "Warranty Replacement" in str(n): print("      row:", n, flush=True)
            pg.screenshot(path=N.EV+f"/archived_status_{status_value or 'blank'}.png", full_page=True)
        b.close()

for sv in ["", "archived", "Archived", "inactive", "Inactive", "deleted", "all", "0", "1"]:
    try: run(sv)
    except Exception as e: print(f"status={sv!r} -> ERR {str(e)[:90]}", flush=True)
json.dump(RESULTS, open(N.EV+"/status_probe.json","w"), indent=1, default=str)
