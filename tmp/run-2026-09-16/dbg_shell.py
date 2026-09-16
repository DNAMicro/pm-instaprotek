import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
def settle(pg,n,s=90):
    for _ in range(int(s/3)):
        pg.wait_for_timeout(3000)
        if n in pg.inner_text("body"): return True
    return False
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050}).new_page()
    for route,filt in [("/portal/product-category","Filter Product Categories"),("/portal/brand","Filter Brands")]:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000); settle(pg,filt)
        print(f"\n=== {route} rows={pg.locator('.md-table-row.table-row').count()}", flush=True)
        op=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
          if(a){a.click();return 'action';} r.click(); return 'row';}""")
        pg.wait_for_timeout(18000)
        info=pg.evaluate("""()=>({full:document.querySelectorAll('.md-dialog--full-page').length,
          adv:document.querySelectorAll('.advancedFullDialog').length,
          dlg:document.querySelectorAll('.md-dialog').length,
          role:document.querySelectorAll('[role=dialog]').length,
          topcls:[...document.querySelectorAll('.md-dialog,[role=dialog],[class*=Dialog],[class*=dialog]')].slice(0,6).map(e=>e.className.toString().slice(0,90))})""")
        print("  open:",op,"|",info, flush=True)
        print("  tabs:", pg.evaluate("()=>[...document.querySelectorAll('.md-tab-label')].map(e=>e.textContent.trim()).filter(Boolean)"), flush=True)
        pg.screenshot(path=N.EV+"/shell_"+route.split('/')[-1]+".png")
    b.close()
