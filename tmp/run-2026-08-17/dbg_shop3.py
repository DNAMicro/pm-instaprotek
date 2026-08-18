import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.click_tab(pg,"Products")
    pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(9000)
    N.click_tab(pg,"Shop Setup"); pg.wait_for_timeout(3500)
    pg.evaluate("""()=>{const c=document.querySelector('.md-dialog--full-page #is_claim_order');if(c&&!c.checked)(c.closest('label')||c).click();}""")
    pg.wait_for_timeout(4500)
    print("react-select ids:", pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('.Select')].filter(s=>s.offsetParent!==null).map(s=>({
        id:(s.querySelector('input')||{}).id||null,
        ph:(s.querySelector('.Select-placeholder')||{}).textContent||null,
        multi:s.className.includes('multi')}));}"""))
    print("\nreact-md toggles:", pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('[id$=-toggle]')].filter(e=>e.offsetParent!==null).map(e=>({id:e.id,txt:e.textContent.trim().slice(0,24)}));}"""))
    print("\ncontenteditable count:", pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('[contenteditable=true]')].map(e=>({vis:e.offsetParent!==null,cls:(e.className||'').toString().slice(0,40)}));}"""))
    print("\nall visible input ids:", pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('input,textarea')].filter(i=>i.offsetParent!==null&&i.type!=='hidden').map(i=>i.id||i.type);}"""))
    b.close()
