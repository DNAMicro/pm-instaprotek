import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050}).new_page()
    for route in ["/portal/repair-network","/portal/company"]:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(20000)
        t=pg.inner_text("body")
        print("=== ",route," url=",pg.url)
        print("ROWS:", pg.locator(".md-table-row.table-row").count(), "| addNew:", pg.get_by_text("addNew").count())
        print("BODY[:1500]:", t[:1500].replace("\n"," | "))
        pg.screenshot(path=N.EV+"/dbg_"+route.split("/")[-1]+".png", full_page=False)
    b.close()
