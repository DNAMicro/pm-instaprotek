import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(9000)
    print("url:", pg.url, "tabs:", N.tabs(pg))
    print("\nfields in plan record:")
    print(pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');if(!d)return[];
      return [...d.querySelectorAll('input,textarea')].filter(e=>e.type!=='hidden').map(e=>({
        id:e.id||null,type:e.type,dis:e.disabled,ro:e.readOnly,vis:e.offsetParent!==null,
        sel:!!e.closest('.Select'),val:(e.value||'').slice(0,22)}));}"""))
    b.close()
