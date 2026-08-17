import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/regions", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.add_new_grid(pg)
    cs=S.controls(pg)
    print("CONTROLS:")
    for c in cs: print("  ", c)
    print("\nscores vs 'region name':")
    for c in cs:
        print("  ", repr(c['label']), "id=",c['id'], "type=",c['type'], "->", S._score(c['label'],'region name'))
    print("\nfind_control(types) ->", S.find_control(pg,'region name',types=["text","email","tel","number","textarea","TEXTAREA"]))
    print("find_control(any)   ->", S.find_control(pg,'region name'))
    b.close()
