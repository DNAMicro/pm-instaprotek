import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/coverage-type", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    print("total rows:", pg.locator(".md-table-row.table-row").count())
    for term in ["RegressionTest0817","RegressionTest0817-EDIT","RegressionTest","Regression"]:
        n=N.search_grid(pg, term)
        print(f"  search {term!r} -> {n} rows")
        if n:
            for i in range(min(n,3)):
                print("     ", pg.locator(".md-table-row.table-row").nth(i).inner_text().replace("\n"," | ")[:110])
    # clear search and list all
    N.search_grid(pg,"")
    pg.wait_for_timeout(2000)
    print("\nall coverage types:", pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.split('\\n')[0].trim()).slice(0,15)"""))
    b.close()
