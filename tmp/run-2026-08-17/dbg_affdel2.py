import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    net=[]; errs=[]
    pg.on("response", lambda r: net.append(f"{r.request.method} {r.status} {r.url[-55:]}"))
    pg.on("console", lambda m: errs.append(m.text[:110]) if m.type=="error" else None)
    pg.goto(N.BASE+"/portal/affiliate", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.search_grid(pg,"RegressionTest")
    net.clear(); errs.clear()
    # use a real Playwright click on the row's delete control
    loc=pg.locator(".md-table-row.table-row").first.locator("button, i.material-icons").filter(has_text="delete").first
    print("delete control count:", pg.locator(".md-table-row.table-row").first.locator("button").count())
    try:
        loc.click(timeout=15000); print("playwright click ok")
    except Exception as e: print("click err", str(e)[:90])
    pg.wait_for_timeout(7000)
    print("network:", [x for x in net if 'DELETE' in x or ' 4' in x or ' 5' in x][:6])
    print("console errors:", errs[:3])
    print("dialogs:", pg.locator(".md-dialog").count())
    print("body has 'sure':", "sure" in pg.inner_text("body").lower())
    n=N.search_grid(pg,"RegressionTest"); print("rows after:", n)
    b.close()
