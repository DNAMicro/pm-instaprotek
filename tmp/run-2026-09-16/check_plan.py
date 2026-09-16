import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PID="d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a"
def settle(pg,n,s=120):
    for _ in range(int(s/3)):
        pg.wait_for_timeout(3000)
        if n in pg.inner_text("body"): return True
    return False
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050}).new_page()
    # 1. direct record URL
    pg.goto(f"{N.BASE}/portal/product-plans/{PID}", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(25000)
    t=pg.inner_text("body")
    print("=== DIRECT RECORD URL ===")
    print("url:", pg.url)
    print("bodylen:", len(t))
    print("body:", t[:700].replace("\n"," | "))
    pg.screenshot(path=N.EV+"/plan_check_record.png")
    # 2. grid: total count + search for the plan name
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
    settle(pg,"Filter Plans")
    pg.wait_for_timeout(10000)
    print("\n=== GRID ===")
    print("pagination:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of \\d+/);return m?m[0]:'not found';}"""))
    for term in ["Years Warranty Replacement","RegressionTest0916"]:
        s=pg.locator("input[placeholder*='Search']").first
        s.fill(""); pg.wait_for_timeout(3000); s.fill(term); pg.wait_for_timeout(14000)
        rows=pg.locator(".md-table-row.table-row").count()
        txt=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].slice(0,8).map(r=>r.innerText.replace(/\\s+/g,' ').trim())""")
        print(f"\nsearch '{term}' -> {rows} row(s)")
        for x in txt: print("   ", x[:130])
    pg.screenshot(path=N.EV+"/plan_check_grid.png")
    b.close()
