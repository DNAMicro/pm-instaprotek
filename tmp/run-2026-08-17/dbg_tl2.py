import sys, re; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for route,label in [("/portal/product-category","ProductCat"),("/portal/category","DeviceCat")]:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
        pg.wait_for_timeout(8000)
        N.click_tab(pg,"Timeline"); pg.wait_for_timeout(4000)
        sets=pg.evaluate("""()=>[...document.querySelectorAll('.dnaTable2-headerSet-item')].map((e,i)=>({i,t:e.innerText.trim().slice(0,18)}))""")
        print(f"\n{label} timeline filter sets:", sets)
        # click the one titled All Activity via its li
        ok=pg.evaluate("""()=>{const els=[...document.querySelectorAll('.dnaTable2-headerSet-item')];
          const e=els.find(x=>/All Activity/.test(x.innerText)); if(!e)return false;
          const a=e.querySelector('a')||e; a.click(); return true;}""")
        pg.wait_for_timeout(5000)
        feed=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
          return p.length?p[0].innerText.slice(0,280).replace(/\\n/g,' | '):'';}""")
        acts=sorted(set(re.findall(r'(Create|Update|Delete)\s+\w+', feed)))
        print(f"  clicked All Activity={ok} acts={acts}")
        print("  feed:", feed[:200])
    b.close()
