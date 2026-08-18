import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
FULL=".md-dialog--full-page"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Details"); pg.wait_for_timeout(2000)
    # ensure required fields are populated
    for fid,val in [("company_code","REGTEST0817"),("first_name","RegressionTest"),
                    ("last_name","CompanyAug17"),("email","regressiontest_co_0817@qamail.test"),("phone","4155550199")]:
        L=pg.locator(f"{FULL} #{fid}")
        if L.count() and not L.first.input_value(): L.first.fill(val); pg.wait_for_timeout(300)
    for _ in range(3):
        rem=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
          return [...d.querySelectorAll('.Select')].filter(s=>{{
            const lbl=((s.querySelector('.Select-placeholder')||{{}}).textContent||'');
            const val=((s.querySelector('.Select-value-label')||{{}}).textContent||'');
            return /\\*/.test(lbl)&&!val;}}).map(s=>(s.querySelector('input')||{{}}).id||null).filter(Boolean);}}""")
        if not rem: break
        for fid in rem:
            try:
                o=N.rs_open(pg,fid,FULL)
                if o: N.rs_pick(pg)
            except Exception: pass
    # set Inactive
    try:
        o=N.md_open(pg,"status-toggle")
        if o: print("picked:", N.md_pick(pg,"Inactive"))
    except Exception as e: print("status err", str(e)[:60])
    pg.wait_for_timeout(1500)
    print("status before save:", pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #status');return e?e.value:null;}}"""))
    sv=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
    pg.wait_for_timeout(9000)
    errs=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,6);}}""")
    print("save:", sv, "errors:", errs)
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    print("status after reload:", pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #status');return e?e.value:null;}}"""))
    b.close()
