"""Create a self-owned test registration on nullnet so claim/email scenarios never touch a real customer."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
IMG="/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/evidence/repair-shops/testlogo.png"

CUST_EMAIL="regressiontest_cust_20260817@qamail.test"
FIRST="RegressionTest"; LAST="CustomerAug17"
PHONE="4155550199"

def dump(pg, tag):
    scope=".md-dialog"
    print(f"\n--- {tag} ---", flush=True)
    print("  step text:", pg.inner_text(scope)[:260].replace("\n"," | "), flush=True)
    print("  fields:", pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');if(!d)return[];
      return [...d.querySelectorAll('input,textarea')].filter(e=>e.type!=='hidden'&&e.type!=='checkbox')
        .map(e=>e.id||e.placeholder||e.type);}}"""), flush=True)
    print("  selects:", pg.evaluate(f"""()=>[...document.querySelectorAll('{scope} .Select')].map(s=>
      s.querySelector('.Select-placeholder')?.textContent.trim()||s.querySelector('.Select-value-label')?.textContent.trim())"""), flush=True)
    print("  buttons:", pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');
      return d?[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean).slice(-8):[];}}"""), flush=True)

def rs_pick(pg, fid, text=None):
    c=pg.locator(f".md-dialog #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
    c.scroll_into_view_if_needed(); c.click(); pg.wait_for_timeout(1400)
    o=(pg.locator(".Select-menu-outer .Select-option", has_text=text).first if text
       else pg.locator(".Select-menu-outer .Select-option").first)
    o.wait_for(state="visible", timeout=8000); t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(900)
    return t

def click_btn(pg, rx):
    return pg.evaluate(f"""()=>{{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/{rx}/i.test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}} return null;}}""")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100})
    pg=ctx.new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(5000)
    dump(pg,"STEP 1 (Search Customer / new customer)")

    # fill the NEW-customer block rather than selecting a real one
    pg.locator(".md-dialog #email").fill(CUST_EMAIL)
    pg.locator(".md-dialog #first_name").fill(FIRST)
    pg.locator(".md-dialog #last_name").fill(LAST)
    try: print("  country:", rs_pick(pg,"country_lu","United States"))
    except Exception as e: print("  country err", str(e)[:70])
    try: print("  code:", rs_pick(pg,"phone_code","US"))
    except Exception as e: print("  code err", str(e)[:70])
    pg.locator(".md-dialog #mobile_phone").fill(PHONE)
    pg.wait_for_timeout(800)
    print("  validate ->", click_btn(pg,"Validate")); pg.wait_for_timeout(4000)
    print("  after validate:", pg.inner_text(".md-dialog")[:200].replace("\n"," | "))
    print("  next ->", click_btn(pg,"Next")); pg.wait_for_timeout(4500)

    for step in range(2,8):
        dump(pg,f"STEP {step}")
        # generic fill for this step
        ids=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');if(!d)return[];
          return [...d.querySelectorAll('input')].filter(e=>['text','email','number'].includes(e.type)&&!e.closest('.Select')&&e.id&&!/search/i.test(e.id))
            .map(e=>({id:e.id,val:e.value}));}""")
        for f in ids:
            fid=f["id"]
            if f["val"]: continue
            v={"barcode":"REGTEST0817001","pin":"123456","receipt_number":"RCPT-0817-TEST",
               "store_name":"RegressionTest Store","branch":"RegressionTest Branch",
               "serial_number":"SN-REGTEST-0817"}.get(fid)
            if v is None: v="RegressionTest"
            try:
                pg.locator(f".md-dialog #{fid}").fill(v); pg.wait_for_timeout(250)
            except Exception: pass
        # any empty react-selects -> pick first
        sels=pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog .Select')].map((s,i)=>
            ({i, ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,
              val:s.querySelector('.Select-value-label')?.textContent.trim()||null,
              id:s.querySelector('input')?.id||null}))""")
        for s in sels:
            if s["val"] or not s["id"]: continue
            try: print(f"    select {s['id']} ->", rs_pick(pg, s["id"]))
            except Exception as e: print(f"    select {s['id']} err", str(e)[:50])
        # radios (survey): pick first of each group
        try:
            pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
              const seen=new Set();
              [...d.querySelectorAll('input[type=radio]')].forEach(r=>{
                 const n=r.name||r.id.slice(0,-1); if(!seen.has(n)){seen.add(n); r.click();}});}""")
            pg.wait_for_timeout(600)
        except Exception: pass
        # receipt upload if present
        try:
            fi=pg.locator(".md-dialog input[type=file]")
            if fi.count(): fi.first.set_input_files(IMG); pg.wait_for_timeout(2500)
        except Exception: pass

        nxt=click_btn(pg,"Next|Submit|Done|Finish|Save")
        print(f"  step{step} advance ->", nxt, flush=True)
        pg.wait_for_timeout(5000)
        body=pg.inner_text("body")
        if any(w in body.lower() for w in ["successfully","registration number","has been created"]):
            print("  >>> CREATION SIGNAL:", [l for l in body.split("\n") if l.strip()][:6], flush=True)
        if pg.locator(".md-dialog").count()==0:
            print("  >>> wizard closed after step", step, flush=True); break

    pg.wait_for_timeout(3000)
    pg.screenshot(path=EV+"/reg_create_end.png", full_page=True)
    print("\nFINAL url:", pg.url)
    print("FINAL body:", pg.inner_text("body")[:400].replace("\n"," | "))
    b.close()
