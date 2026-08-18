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
    print("tabs:", N.tabs(pg))
    N.click_tab(pg,"Shop Setup"); pg.wait_for_timeout(4000)
    print("\nPANEL TEXT:")
    print(pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
      return p.length?p[0].innerText.slice(0,700).replace(/\\n/g,' | '):'';}"""))
    print("\nINPUTS (id/label):")
    print(pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('input,textarea')].filter(i=>i.offsetParent!==null&&i.type!=='hidden').map(i=>{
        const w=i.closest('.md-text-field-container,.md-cell')||i.parentElement;
        return {id:i.id||null,type:i.type,sel:!!i.closest('.Select'),
                lbl:((w?w.innerText:'')||'').split('\\n')[0].slice(0,30)};});}"""))
    print("\nSELECTS:")
    print(pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('.Select')].filter(s=>s.offsetParent!==null).map(s=>({
        id:(s.querySelector('input')||{}).id||null,
        ph:(s.querySelector('.Select-placeholder')||{}).textContent||null}));}"""))
    b.close()
