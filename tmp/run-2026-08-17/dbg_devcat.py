import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.search_grid(pg,"RegressionTest")
    n=pg.locator(".md-table-row.table-row").count()
    print("test category rows:", n)
    if n:
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
        pg.wait_for_timeout(8000)
        print("url:", pg.url)
        print("tabs:", N.tabs(pg))
        N.click_tab(pg,"Devices")
        print("\nbuttons in record:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog--full-page button,.md-dialog--full-page i')]
          .filter(e=>e.offsetParent!==null).map(e=>e.textContent.trim()).filter(Boolean).slice(0,20)"""))
        print("\npanel text:", pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
          return p.length?p[0].innerText.slice(0,260).replace(/\\n/g,' | '):'';}"""))
        # try clicking add
        r=pg.evaluate("""()=>{const els=[...document.querySelectorAll('.md-dialog--full-page button,.md-dialog--full-page i')]
          .filter(e=>/^add$|addNew|Add/.test(e.textContent.trim())&&e.offsetParent!==null);
          if(els.length){els[0].click();return els.map(e=>e.textContent.trim());}return 'none';}""")
        pg.wait_for_timeout(6000)
        print("\nadd click:", r)
        print("dialogs:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog')].map(d=>({full:d.classList.contains('md-dialog--full-page'),txt:d.innerText.slice(0,120).replace(/\\n/g,' | ')}))"""))
    b.close()
