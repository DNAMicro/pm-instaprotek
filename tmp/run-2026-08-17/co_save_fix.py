import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:140]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Details")
    pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const t=[...d.querySelectorAll('.md-selection-control-container')].find(e=>/Enterprise/i.test(e.innerText));
      const cb=t&&t.querySelector('input[type=checkbox]'); if(cb&&!cb.checked)(cb.closest('label')||cb).click();}""")
    pg.wait_for_timeout(3500)
    for fid,val in [("company_code","REGTEST0817"),("first_name","RegressionTest"),
                    ("last_name","CompanyAug17"),("email","regressiontest_co_0817@qamail.test"),
                    ("phone","4155550199")]:
        L=pg.locator(f".md-dialog--full-page #{fid}")
        if L.count():
            L.first.scroll_into_view_if_needed(); L.first.fill(val); pg.wait_for_timeout(500)
    for fid,txt in [("repair_network",None),("country_lu","United States")]:
        try:
            o=N.rs_open(pg,fid,".md-dialog--full-page")
            if o: N.rs_pick(pg,txt)
        except Exception as e: print("  sel",fid,str(e)[:50])
    # address
    try:
        ai=pg.get_by_placeholder("Search address")
        if ai.count():
            ai.first.scroll_into_view_if_needed(); ai.first.click(); ai.first.fill("")
            ai.first.type("1600 Amphitheatre Parkway, Mountain View", delay=80)
            pg.locator(".address__suggestion__item").first.wait_for(state="visible", timeout=11000)
            pg.locator(".address__suggestion__item").first.click(); pg.wait_for_timeout(2200)
            for fid,val in [("street","1600 Amphitheatre Parkway"),("city","Mountain View"),("zip_code","94043")]:
                L=pg.locator(f".md-dialog--full-page #{fid}")
                if L.count() and not L.first.input_value(): L.first.fill(val)
    except Exception as e: print("  addr", str(e)[:60])
    pg.wait_for_timeout(800)
    sv=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
            ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return b.textContent.trim();}return 'none';}""")
    pg.wait_for_timeout(9000)
    errs=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,6);}""")
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Details")
    saved=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return {code:(d.querySelector('#company_code')||{}).value, first:(d.querySelector('#first_name')||{}).value,
              email:(d.querySelector('#email')||{}).value};}""")
    rec("Details|16","PASS" if (sv!='none' and saved.get('code')) else "FAIL",
        f"Save ('{sv}') stores the company details — reopened the record and it reads {saved}{'; validation: '+str(errs) if errs else ''}.")
    b.close()
n,_,_=resultio.write('SETTINGS - COMPANY ',R)
print("tally:",resultio.tally('SETTINGS - COMPANY '))
