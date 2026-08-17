import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(9500)
    N.click_tab(pg,"Repair Receipt"); pg.wait_for_timeout(4500)
    print("BEFORE check — selects:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog--full-page .Select')].filter(s=>s.offsetParent!==null)
      .map(s=>({cls:s.className.slice(0,50), id:s.querySelector('input')?.id||null, ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null}))"""))
    c=pg.evaluate("""()=>{const c=document.querySelector('#is_customer_using_insurance');
      if(!c)return 'no cb'; if(!c.checked)(c.closest('label')||c).click(); return c.checked;}""")
    pg.wait_for_timeout(3500)
    print("checkbox now:", c)
    print("AFTER check — selects:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog--full-page .Select')].filter(s=>s.offsetParent!==null)
      .map(s=>({cls:s.className.slice(0,50), id:s.querySelector('input')?.id||null, ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null}))"""))
    print("device_insurance element:", pg.evaluate("""()=>{const e=document.querySelector('#device_insurance');
      return e?{tag:e.tagName,type:e.type,vis:e.offsetParent!==null,inSel:!!e.closest('.Select'),parent:e.parentElement.className.slice(0,50)}:null;}"""))
    # try opening via the Select-control of the select that owns device_insurance
    r=pg.evaluate("""()=>{const e=document.querySelector('#device_insurance');
      const s=e?e.closest('.Select'):[...document.querySelectorAll('.md-dialog--full-page .Select')].filter(x=>x.offsetParent!==null)[0];
      if(!s)return 'no select'; s.scrollIntoView({block:'center'}); const c=s.querySelector('.Select-control'); if(c){c.click();return 'clicked';} return 'no control';}""")
    pg.wait_for_timeout(2200)
    print("open ->", r, "options:", N.opts(pg))
    print("\ncovered_amount:", pg.evaluate("""()=>{const e=document.querySelector('#covered_amount');
      return e?{type:e.type,dis:e.disabled,ro:e.readOnly,val:e.value,cls:e.className.slice(0,40)}:null;}"""))
    print("repair_amount:", pg.evaluate("""()=>{const e=document.querySelector('#repair_amount');
      return e?{type:e.type,dis:e.disabled,ro:e.readOnly,val:e.value}:null;}"""))
    b.close()
