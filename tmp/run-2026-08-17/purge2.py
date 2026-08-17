"""Purge RegressionTest records from record-based settings grids (open record -> Delete -> Yes)."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
ROUTES=sys.argv[1:]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for route in ROUTES:
        for attempt in range(5):
            pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
            n=N.search_grid(pg,"RegressionTest")
            if n<=0: break
            name=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.replace(/\\s+/g,' ').trim().slice(0,60):null;}""")
            # try row delete action first
            d=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='delete');
              if(a){a.click();return 'row-delete';}return 'no-row-delete';}""")
            pg.wait_for_timeout(3000)
            if d=='no-row-delete':
                pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
                  const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
                pg.wait_for_timeout(7000)
                pg.evaluate("""()=>{const dl=document.querySelector('.md-dialog--full-page');
                  const b=[...dl.querySelectorAll('button')].find(x=>/Delete/i.test(x.textContent));if(b)b.click();}""")
                pg.wait_for_timeout(3000)
            txt=N.sub_text(pg) or ""
            if "Yes" in txt:
                pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
                  const d=ds[ds.length-1];const b=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(b)b.click();}""")
                pg.wait_for_timeout(7000)
            print(f"  {route}: removed {name!r} via {d}", flush=True)
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7000)
        print(f"  {route}: RegressionTest rows remaining = {N.search_grid(pg,'RegressionTest')}", flush=True)
    b.close()
