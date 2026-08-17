"""Delete any leftover RegressionTest records from a settings grid."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
ROUTES=sys.argv[1:] or ["/portal/coverage-type"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for route in ROUTES:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        for _ in range(6):
            n=N.search_grid(pg,"RegressionTest")
            if n==0: break
            row=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.split('\\n')[0].trim():null;}""")
            d=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete/.test(e.textContent));
              if(a){a.click();return 'clicked';}return 'no-del';}""")
            pg.wait_for_timeout(3000)
            dlg=N.sub_text(pg) or ""
            if "Yes" in dlg:
                pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('md-dialog--full-page'));
                  const d=ds[ds.length-1];const b=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(b)b.click();}""")
                pg.wait_for_timeout(6000)
            print(f"  {route}: deleted {row!r} ({d})", flush=True)
        left=N.search_grid(pg,"RegressionTest")
        print(f"  {route}: RegressionTest rows remaining = {left}", flush=True)
    b.close()
