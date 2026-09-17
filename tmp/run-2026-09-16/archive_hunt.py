"""READ-ONLY. Look for an archive view for plans: UI affordances + the API calls the grid makes."""
import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PID="d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    calls=[]
    pg.on("request", lambda r: calls.append((r.method, r.url)) if ("/api" in r.url or "plan" in r.url.lower()) and "static" not in r.url else None)
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
    for _ in range(45):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    print("=== API CALLS MADE BY THE PLANS GRID ===", flush=True)
    for m,u in calls[:25]: print(f"  {m} {u[:190]}", flush=True)

    print("\n=== ALL TABS / TOGGLES / BUTTONS ON THE GRID ===", flush=True)
    ui=pg.evaluate("""()=>{
      const grab=(sel)=>[...document.querySelectorAll(sel)].map(e=>(e.innerText||e.textContent||'').trim()).filter(t=>t&&t.length<50);
      return {tabs:grab('.md-tab-label, [role=tab]'),
              buttons:[...new Set(grab('button'))],
              checkboxes:[...document.querySelectorAll('input[type=checkbox]')].map(e=>({id:e.id,checked:e.checked,
                 lbl:((e.closest('.md-cell,label,div')||{}).innerText||'').split('\\n')[0].trim().slice(0,40)})),
              menuish:[...new Set(grab('[class*=menu] li, [class*=Menu] li, .md-list-tile'))]};}""")
    for k,v in ui.items(): print(f"  {k}: {v}", flush=True)

    print("\n=== ARCHIVE-ISH WORDS ANYWHERE ON THE PAGE ===", flush=True)
    body=pg.inner_text("body")
    print("  ", [w for w in ["Archive","Archived","Inactive","Deleted","Trash","Restore","Show all","Status"] if w.lower() in body.lower()], flush=True)

    print("\n=== CANDIDATE ARCHIVE ROUTES / PARAMS ===", flush=True)
    for route in ["/portal/product-plans?archived=true","/portal/product-plans/archived","/portal/product-plans/archive",
                  "/portal/archive","/portal/archived","/portal/product-plans?status=archived","/portal/product-plans?isActive=false"]:
        try:
            pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
            t=pg.inner_text("body")
            pag=pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'-';}""")
            lost="LOOKS LIKE YOU'RE LOST" in t.upper() or "No records found" in t
            print(f"  {route:44s} -> pag={pag:14s} lost={lost} hasPlan={'Years Warranty Replacement' in t}", flush=True)
        except Exception as e:
            print(f"  {route:44s} -> ERR {str(e)[:50]}", flush=True)
    b.close()
