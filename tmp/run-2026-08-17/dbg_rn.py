import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    for route,flt in [("/portal/repair-network","Filter Repair Network"),("/portal/support","Filter Supports")]:
        pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
        errs=[]
        pg.on("console", lambda m,E=errs: E.append(m.text[:100]) if m.type=="error" else None)
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        print(f"\n=== {route} rows={pg.locator('.md-table-row.table-row').count()}")
        pg.get_by_text(flt).first.click(); pg.wait_for_timeout(2200)
        cols=N.rs_open_ph(pg,"Select a filter"); print("  columns:", cols)
        for c in cols[:3]:
            try:
                N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,c); pg.wait_for_timeout(2500)
            except Exception as e:
                print(f"   {c}: pick err {str(e)[:50]}"); continue
            blank=len(pg.inner_text("body").strip())==0
            vals=[]
            try: vals=N.rs_open_ph(pg,"Select a value")
            except Exception: pass
            print(f"   {c}: blank={blank} values={vals[:6]} err={errs[-1][:70] if errs else None}")
            if blank:
                pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7000)
                pg.get_by_text(flt).first.click(); pg.wait_for_timeout(2000)
        pg.close()
    b.close()
