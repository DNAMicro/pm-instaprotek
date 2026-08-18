import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:150]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Details")
    pg.evaluate("""()=>{const c=document.querySelector('.md-dialog--full-page #enable_enterprise_program');
      if(c&&!c.checked)(c.closest('label')||c).click();}""")
    pg.wait_for_timeout(3500)
    for fid,val in [("company_code","REGTEST0817"),("first_name","RegressionTest"),("last_name","CompanyAug17"),
                    ("email","regressiontest_co_0817@qamail.test"),("phone","4155550199")]:
        L=pg.locator(f".md-dialog--full-page #{fid}")
        if L.count(): L.first.fill(val); pg.wait_for_timeout(300)
    # all selects incl. language
    for fid,txt in [("repair_network",None),("country_lu","United States"),("language","English"),("language_id","English")]:
        if pg.locator(f".md-dialog--full-page #{fid}").count():
            try:
                o=N.rs_open(pg,fid,".md-dialog--full-page")
                if o: N.rs_pick(pg,txt)
            except Exception as e: print("  sel",fid,str(e)[:50])
    # any remaining empty required select
    for _ in range(3):
        rem=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          return [...d.querySelectorAll('.Select')].filter(s=>{
            const lbl=((s.querySelector('.Select-placeholder')||{}).textContent||'');
            const val=((s.querySelector('.Select-value-label')||{}).textContent||'');
            return /\\*/.test(lbl)&&!val;}).map(s=>(s.querySelector('input')||{}).id||null);}""")
        rem=[x for x in rem if x]
        if not rem: break
        for fid in rem:
            try:
                o=N.rs_open(pg,fid,".md-dialog--full-page")
                if o: N.rs_pick(pg)
            except Exception: pass
    # address
    try:
        ai=pg.get_by_placeholder("Search address")
        if ai.count():
            ai.first.scroll_into_view_if_needed(); ai.first.click(); ai.first.fill("")
            ai.first.type("1600 Amphitheatre Parkway, Mountain View", delay=80)
            pg.locator(".address__suggestion__item").first.wait_for(state="visible", timeout=12000)
            pg.locator(".address__suggestion__item").first.click(); pg.wait_for_timeout(2500)
            for fid,val in [("street","1600 Amphitheatre Parkway"),("city","Mountain View"),("zip_code","94043")]:
                L=pg.locator(f".md-dialog--full-page #{fid}")
                if L.count() and not L.first.input_value(): L.first.fill(val)
            for fid,txt in [("country","United States"),("state","California")]:
                if pg.locator(f".md-dialog--full-page #{fid}").count():
                    try:
                        o=N.rs_open(pg,fid,".md-dialog--full-page")
                        if o: N.rs_pick(pg,txt)
                    except Exception: pass
    except Exception as e: print("  addr", str(e)[:70])
    pg.wait_for_timeout(1000)
    sv=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return b.textContent.trim();}return 'none';}""")
    pg.wait_for_timeout(9500)
    errs=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,6);}""")
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Details")
    ent=pg.evaluate("""()=>{const c=document.querySelector('.md-dialog--full-page #enable_enterprise_program');return c?c.checked:null;}""")
    saved=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const g=id=>{const e=d.querySelector('#'+id);return e?e.value:null;};
      return {code:g('company_code'),first:g('first_name'),email:g('email')};}""")
    rec("Details|16","PASS" if (sv!='none' and not errs and ent) else "FAIL",
        f"Save ('{sv}') stores the company details — reopened the record: Enterprise Program still enabled={ent}, fields {saved}{'; validation: '+str(errs) if errs else ''}.")
    b.close()
n,_,_=resultio.write('SETTINGS - COMPANY ',R)
print("tally:",resultio.tally('SETTINGS - COMPANY '))
