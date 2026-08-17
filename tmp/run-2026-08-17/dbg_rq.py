import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/review-questions", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.add_new_grid(pg)
    print("controls:", S.controls(pg))
    print("buttons:", N.sub_btns(pg))
    for phrase,val in [("title","RegressionTest0817"),("question","RegressionTest0817"),("option","RegressionTest0817")]:
        print(" ",phrase, S.act_input(pg,phrase,val))
    print("\nbefore Done:", N.sub_text(pg)[:220].replace("\n"," | "))
    print("Done ->", N.sub_click(pg,"^Done$")); pg.wait_for_timeout(2500)
    print("after Done:", N.sub_text(pg)[:260].replace("\n"," | "))
    print("controls after Done:", S.controls(pg))
    r,still,errs=S.save(pg)
    print("\nsave:",r,"still:",still,"errs:",errs)
    print("modal now:", (N.sub_text(pg) or '')[:220].replace("\n"," | "))
    b.close()
