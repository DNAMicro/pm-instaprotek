import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for route,fid in [("/portal/regions","Region"),("/portal/administrators",None),("/portal/underwriters",None)]:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        N.add_new_grid(pg)
        print(f"\n=== {route} ===")
        for c in S.controls(pg): print("   ", c)
        # try opening any select
        try:
            o=pg.evaluate(f"""()=>{{const d={N.SUB};const s=d.querySelector('.Select');
              if(s){{s.scrollIntoView({{block:'center'}});s.querySelector('.Select-control').click();return true;}}return false;}}""")
            pg.wait_for_timeout(1800)
            print("   options:", N.opts(pg)[:12])
            # can we type into it?
            inp=pg.locator(".md-dialog:not(.md-dialog--full-page) .Select input").first
            inp.type("RegressionTest0817", delay=40); pg.wait_for_timeout(1500)
            print("   after typing, options:", N.opts(pg)[:6])
            print("   input value:", inp.input_value())
        except Exception as e: print("   err", str(e)[:80])
        N.sub_click(pg,"Cancel"); pg.wait_for_timeout(1500)
    b.close()
