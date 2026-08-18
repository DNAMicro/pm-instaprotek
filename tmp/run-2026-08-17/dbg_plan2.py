import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    s=pg.get_by_placeholder("Search Plans...")
    base=pg.locator(".md-table-row.table-row").count()
    print("baseline rows:", base)
    for term in ["Demo Plan 100","Camera","zzzzzz"]:
        s.first.fill(""); pg.wait_for_timeout(2000); s.first.fill(term)
        for w in (4,8):
            pg.wait_for_timeout(4000)
            n=pg.locator(".md-table-row.table-row").count()
            first=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.split('\\n')[0].trim():'';}""")
            print(f"  {term!r} @{w}s -> rows={n} first={first[:40]!r}")
    # compare with a grid where search worked (coverage-type)
    pg.goto(N.BASE+"/portal/coverage-type", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    c0=pg.locator(".md-table-row.table-row").count()
    cs=pg.get_by_placeholder("Search Coverage Types...")
    if cs.count()==0: cs=pg.locator("input[placeholder*='Search']")
    cs.first.fill("Camera"); pg.wait_for_timeout(5000)
    print(f"  [control] coverage-type: {c0} -> {pg.locator('.md-table-row.table-row').count()} rows after searching 'Camera'")
    b.close()
