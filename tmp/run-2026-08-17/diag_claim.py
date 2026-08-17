import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    print("rows:", pg.locator(".md-table-row.table-row").count())
    print("row actions:", pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      return r?[...r.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim()):null;}"""))
    print("row:", pg.locator(".md-table-row.table-row").first.inner_text().replace("\n"," | ")[:180])
    # 1) the New wizard from the claim grid
    N.add_new_grid(pg); pg.wait_for_timeout(3000)
    print("\n=== NEW CLAIM WIZARD (from grid) ===")
    print("sub text:", N.sub_text(pg)[:320].replace("\n"," | "))
    print("buttons:", N.sub_btns(pg)[-6:])
    N.sub_click(pg,"Cancel|close"); pg.wait_for_timeout(2500)
    # 2) open an existing claim
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    r=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/find_in_page|edit/.test(e.textContent));
      if(a){a.click();return a.textContent.trim();} r.click(); return 'row';}""")
    pg.wait_for_timeout(9000)
    print("\n=== CLAIM RECORD (opened via", r, ") ===")
    print("url:", pg.url)
    print("tabs:", N.tabs(pg))
    print("body head:", pg.inner_text("body")[:500].replace("\n"," | "))
    b.close()
