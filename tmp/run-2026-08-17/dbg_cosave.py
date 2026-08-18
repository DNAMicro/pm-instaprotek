import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Details")
    print("enterprise checkbox state on load:", pg.evaluate("""()=>{const c=document.querySelector('.md-dialog--full-page #enable_enterprise_program');return c?c.checked:null;}"""))
    pg.evaluate("""()=>{const c=document.querySelector('.md-dialog--full-page #enable_enterprise_program');
      if(c&&!c.checked)(c.closest('label')||c).click();}""")
    pg.wait_for_timeout(3500)
    for fid,val in [("company_code","REGTEST0817"),("first_name","RegressionTest"),("last_name","CompanyAug17"),
                    ("email","regressiontest_co_0817@qamail.test"),("phone","4155550199")]:
        L=pg.locator(f".md-dialog--full-page #{fid}")
        if L.count(): L.first.fill(val)
    for fid,txt in [("repair_network",None),("country_lu","United States")]:
        try:
            o=N.rs_open(pg,fid,".md-dialog--full-page")
            if o: N.rs_pick(pg,txt)
        except Exception: pass
    pg.wait_for_timeout(800)
    print("\nfilled values:", pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const g=id=>{const e=d.querySelector('#'+id);return e?(e.closest('.Select')?((e.closest('.Select').querySelector('.Select-value-label')||{}).textContent||''):e.value):null;};
      return {code:g('company_code'),first:g('first_name'),last:g('last_name'),email:g('email'),phone:g('phone'),rn:g('repair_network'),country:g('country_lu')};}"""))
    pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled);if(b)b.click();}""")
    pg.wait_for_timeout(9000)
    print("\nafter save — url:", pg.url)
    print("errors:", pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');if(!d)return 'no-record-dialog';
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,8);}"""))
    print("body snippet:", pg.inner_text("body")[:200].replace("\n"," | "))
    b.close()
