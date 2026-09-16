import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N, guard
from playwright.sync_api import sync_playwright
CASES=[("REAL production plan","/portal/product-plans/","first-row"),
       ("OUR brand record","/portal/brand/c16268e4-4dac-44af-850d-8c9747e19b58",None)]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050}).new_page()
    # our own record
    pg.goto(N.BASE+"/portal/brand/c16268e4-4dac-44af-850d-8c9747e19b58", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(25000)
    try:
        guard.assert_ours(pg,"test"); print("OUR record      -> ALLOWED (correct)")
    except guard.NotOurs as e: print("OUR record      -> BLOCKED (WRONG):", str(e)[:120])
    # a real production plan (open first grid row)
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
    for _ in range(40):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(22000)
    hdr=(guard.record_text(pg) or "")[:90].replace("\n"," | ")
    print("opened real record:", hdr)
    try:
        guard.assert_ours(pg,"test"); print("REAL record     -> ALLOWED (WRONG - guard failed!)")
    except guard.NotOurs as e: print("REAL record     -> BLOCKED (correct):", str(e)[:130])
    ok,msg=guard.safe_delete(pg,"real plan")
    print("safe_delete on REAL record ->", ok, "|", msg[:130])
    b.close()
