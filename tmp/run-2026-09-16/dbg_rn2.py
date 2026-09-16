import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050})
    pg=ctx.new_page()
    errs=[]
    pg.on("console", lambda m: errs.append(("console",m.type,m.text[:200])) if m.type in ("error","warning") else None)
    pg.on("pageerror", lambda e: errs.append(("pageerror","",str(e)[:250])))
    pg.on("response", lambda r: errs.append(("http",str(r.status),r.url[:160])) if r.status>=400 else None)
    for route in ["/portal/regions","/portal/repair-network"]:
        errs.clear()
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(35000)
        t=pg.inner_text("body")
        print(f"\n=== {route}  url={pg.url}")
        print("BODYLEN:", len(t), "| ROWS:", pg.locator(".md-table-row.table-row").count(), "| addNew:", pg.get_by_text('addNew').count())
        print("BODY:", t[:600].replace("\n"," | "))
        print("ROOT HTML len:", pg.evaluate("()=>document.body.innerHTML.length"))
        for e in errs[:14]: print("  ", e)
        pg.screenshot(path=N.EV+"/dbg2_"+route.split('/')[-1]+".png", full_page=False)
    b.close()
