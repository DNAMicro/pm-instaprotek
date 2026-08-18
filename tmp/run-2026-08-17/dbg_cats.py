import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Products"); N.add_new_in_record(pg)
    # BEFORE selecting a plan
    try:
        o=N.rs_open(pg,"categories",".md-dialog:not(.md-dialog--full-page)")
        print("categories BEFORE plan:", o[:10])
    except Exception as e: print("before err", str(e)[:60])
    # select plan then retry with waits
    try:
        N.rs_open(pg,"plan",".md-dialog:not(.md-dialog--full-page)"); N.rs_pick(pg)
    except Exception as e: print("plan err", str(e)[:60])
    for w in (2,6,12):
        pg.wait_for_timeout(4000)
        try:
            o=N.rs_open(pg,"categories",".md-dialog:not(.md-dialog--full-page)")
            print(f"categories AFTER plan @~{w}s:", o[:10])
            if o: break
        except Exception as e: print("  err", str(e)[:50])
    # is it multi-select needing typing?
    print("\ncategories element:", pg.evaluate(f"""()=>{{const d={N.SUB};const e=d.querySelector('#categories');
      return e?{{cls:e.closest('.Select').className, ph:(e.closest('.Select').querySelector('.Select-placeholder')||{{}}).textContent}}:null;}}"""))
    try:
        inp=pg.locator(".md-dialog:not(.md-dialog--full-page) #categories")
        inp.click(); inp.type("Chrome", delay=60); pg.wait_for_timeout(2500)
        print("after typing 'Chrome':", N.opts(pg)[:8])
    except Exception as e: print("type err", str(e)[:60])
    b.close()
