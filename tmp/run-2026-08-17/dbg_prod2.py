import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    names=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.split('\\n')[0].trim())""")
    print("product categories:", names)
    for i in range(min(3,len(names))):
        pg.goto(N.BASE+"/portal/product-category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        pg.evaluate(f"""()=>{{const rows=[...document.querySelectorAll('.md-table-row.table-row')];const r=rows[{i}];
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}}""")
        pg.wait_for_timeout(8000)
        N.click_tab(pg,"Products")
        add=pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog--full-page button,.md-dialog--full-page i')]
          .filter(e=>/add/i.test(e.textContent)&&e.offsetParent!==null).map(e=>e.textContent.trim())""")
        rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
        print(f"  '{names[i]}': product rows={rows} add-controls={add}")
    b.close()
