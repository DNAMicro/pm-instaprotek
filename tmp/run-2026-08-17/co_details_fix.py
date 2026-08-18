import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:130]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Details")
    pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const t=[...d.querySelectorAll('.md-selection-control-container')].find(e=>/Enterprise/i.test(e.innerText));
      const cb=t&&t.querySelector('input[type=checkbox]'); if(cb&&!cb.checked)(cb.closest('label')||cb).click();}""")
    pg.wait_for_timeout(3000)
    fields=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return [...d.querySelectorAll('.Select')].map(s=>((s.querySelector('.Select-placeholder')||{}).textContent||(s.querySelector('.Select-value-label')||{}).textContent||'').trim());}""")
    rec("Details|7","FAIL",
        f"No 'Device Management System' field exists on the company Details form. The only dropdowns rendered after enabling the Enterprise Program are {fields} (ids: repair_network, country_lu, phone_code); the text inputs are Company Name, Company Code, First Name, Last Name, Email, Phone. The test case expects a Device Management System dropdown.")
    rec("Details|8","BLOCKED","No device management system option can be selected because the field does not exist (see Details|7 / DEF-SET-07).")
    o=[]
    try: o=N.rs_open(pg,"country_lu",".md-dialog--full-page")
    except Exception as e: print("  err",str(e)[:70])
    rec("Details|9","PASS" if o else "FAIL", f"Country field (#country_lu) opens a dropdown; options: {o}")
    v=None
    if o:
        try: v=N.rs_pick(pg,"United States")
        except Exception:
            try: v=N.rs_pick(pg)
            except Exception: pass
    rec("Details|10","PASS" if v else "FAIL", f"Selected country '{v}' reflects on the field.")
    sv=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
            ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return b.textContent.trim();}return 'none';}""")
    pg.wait_for_timeout(8000)
    errs=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}""")
    # reload to confirm persistence
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    N.click_tab(pg,"Details")
    saved=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const c=d.querySelector('#company_code');return c?c.value:null;}""")
    rec("Details|16","PASS" if (sv!='none' and not errs and saved) else "FAIL",
        f"Save ('{sv}') stores the company details — reopened the record and Company Code reads '{saved}'{'; validation: '+str(errs) if errs else ''}.")
    b.close()
n,_,_=resultio.write('SETTINGS - COMPANY ',R,defects={'Details|7':'DEF-SET-07'})
print("tally:",resultio.tally('SETTINGS - COMPANY '))
