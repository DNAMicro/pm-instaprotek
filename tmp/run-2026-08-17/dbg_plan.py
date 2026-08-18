import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    print("total rows:", pg.locator(".md-table-row.table-row").count())
    print("search field:", pg.evaluate("""()=>[...document.querySelectorAll('input')].map(e=>({id:e.id,ph:e.placeholder,vis:e.offsetParent!==null})).filter(x=>x.ph).slice(0,4)"""))
    s=pg.get_by_placeholder("Search Plans...")
    print("search count:", s.count())
    if s.count():
        s.first.fill("RegressionTest"); pg.wait_for_timeout(5000)
        n=pg.locator(".md-table-row.table-row").count()
        print("rows after search RegressionTest:", n)
        for i in range(min(n,3)):
            print("   ", pg.locator(".md-table-row.table-row").nth(i).inner_text().replace("\n"," | ")[:110])
    # any plan whose text contains RegressionTest across the whole grid?
    hits=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.replace(/\\s+/g,' ').trim()).filter(t=>/RegressionTest/.test(t))""")
    print("rows containing RegressionTest:", hits)
    b.close()
