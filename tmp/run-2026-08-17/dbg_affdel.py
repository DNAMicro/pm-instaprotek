import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/affiliate", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    n=N.search_grid(pg,"RegressionTest"); print("rows:", n)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='delete');if(a)a.click();}""")
    for w in (2,5,9):
        pg.wait_for_timeout(3000)
        info=pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog')].map(d=>({
          full:d.classList.contains('md-dialog--full-page'),
          vis:d.offsetParent!==null,
          txt:d.innerText.slice(0,120).replace(/\\n/g,' | '),
          btns:[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).slice(-4)}))""")
        print(f"  +{w}s dialogs:", info)
        body=pg.inner_text("body")
        if "sure" in body.lower(): print("     body mentions 'sure'")
    b.close()
