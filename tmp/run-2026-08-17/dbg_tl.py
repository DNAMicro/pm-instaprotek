import sys, re; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for route,label in [("/portal/product-category","Product Category"),("/portal/category","Device Category")]:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
        pg.wait_for_timeout(8000)
        N.click_tab(pg,"Timeline"); pg.wait_for_timeout(4000)
        # explicitly click the "All Activity" tab
        clicked=pg.evaluate("""()=>{const t=[...document.querySelectorAll('*')].find(e=>e.textContent.trim()==='All Activity'&&e.children.length===0);
          if(t){(t.closest('button,li,div')||t).click();return true;}return false;}""")
        pg.wait_for_timeout(4500)
        feed=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
          return p.length?p[0].innerText.slice(0,300).replace(/\\n/g,' | '):'';}""")
        acts=sorted(set(re.findall(r'(Create|Update|Delete)\s+\w+', feed)))
        print(f"\n{label}: AllActivity-clicked={clicked} acts={acts}")
        print("   feed:", feed[:220])
        # count custom filter tabs
        cf=pg.evaluate("""()=>[...document.querySelectorAll('*')].filter(e=>e.textContent.trim()==='Custom Filter'&&e.children.length===0).length""")
        print("   custom filter tabs:", cf)
    b.close()
