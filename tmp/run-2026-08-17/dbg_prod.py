import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    n=N.search_grid(pg,"RegressionTest")
    print("test rows:", n)
    if n<=0:
        N.search_grid(pg,"")
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    print("url:",pg.url,"tabs:",N.tabs(pg))
    N.click_tab(pg,"Products")
    print("visible controls in record:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog--full-page button,.md-dialog--full-page i')]
      .filter(e=>e.offsetParent!==null).map(e=>e.textContent.trim()).filter(Boolean).slice(0,18)"""))
    print("panel:", pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
      return p.length?p[0].innerText.slice(0,240).replace(/\\n/g,' | '):'';}"""))
    r=N.add_new_in_record(pg)
    print("\nadd_new_in_record ->", r)
    print("dialogs:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog')].map(d=>({full:d.classList.contains('md-dialog--full-page'),txt:d.innerText.slice(0,110).replace(/\\n/g,' | ')}))"""))
    b.close()
