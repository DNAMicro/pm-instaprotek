import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/survey", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    print("rows:", pg.locator(".md-table-row.table-row").count())
    print("body:", pg.inner_text("body")[:320].replace("\n"," | "))
    print("addNew present:", pg.get_by_text("addNew").count())
    if pg.get_by_text("addNew").count():
        N.add_new_grid(pg)
        print("\nmodal:", (N.sub_text(pg) or '')[:250].replace("\n"," | "))
        print("controls:", S.controls(pg))
        print("buttons:", N.sub_btns(pg))
        N.sub_click(pg,"Cancel")
    b.close()
