import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Details")
    # ensure enterprise enabled
    pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const t=[...d.querySelectorAll('.md-selection-control-container')].find(e=>/Enterprise/i.test(e.innerText));
      const cb=t&&t.querySelector('input[type=checkbox]'); if(cb&&!cb.checked)(cb.closest('label')||cb).click();}""")
    pg.wait_for_timeout(3000)
    print("SELECTS in company details:")
    print(pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('.Select')].map((s,i)=>({i,
        id:(s.querySelector('input')||{}).id||null,
        ph:(s.querySelector('.Select-placeholder')||{}).textContent||null,
        val:(s.querySelector('.Select-value-label')||{}).textContent||null,
        ctx:((s.closest('.md-cell,div')||{}).innerText||'').split('\\n')[0].slice(0,28)}));}"""))
    print("\nall visible inputs:")
    print(pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('input')].filter(i=>i.offsetParent!==null&&i.type!=='hidden').map(i=>({id:i.id,type:i.type,sel:!!i.closest('.Select')}));}"""))
    b.close()
