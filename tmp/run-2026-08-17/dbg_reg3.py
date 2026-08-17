import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/regions", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    print("row actions:", pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      return [...r.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim());}"""))
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(7000)
    print("url:", pg.url)
    print("dialogs:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog')].map(d=>({full:d.classList.contains('md-dialog--full-page'),txt:d.innerText.slice(0,90).replace(/\\n/g,' | ')}))"""))
    print("body:", pg.inner_text("body")[:250].replace("\n"," | "))
    b.close()
