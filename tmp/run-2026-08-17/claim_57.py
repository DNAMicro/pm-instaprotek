"""Re-test PORTAL-REGISTRATION Claim|5,6,7 against the real 3-step wizard (#notes on Step 2)."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
TAB="PORTAL - REGISTRATION"
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:140]}", flush=True)

SUB="""(()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('md-dialog--full-page'));
  return ds.length?ds[ds.length-1]:null;})()"""
def step_of(pg):
    return pg.evaluate(f"""()=>{{const d={SUB};if(!d)return null;
      const m=d.innerText.match(/Step\\s*(\\d)/);return m?m[1]:null;}}""")
def nxt(pg):
    return pg.evaluate(f"""()=>{{const d={SUB};if(!d)return 'no-modal';
      const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);
      if(b){{b.click();return 'clicked';}}return 'no-next';}}""")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    reg=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.match(/\\d{12}/)?.[0]:null;}""")
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Claim');if(t)t.click();}""")
    pg.wait_for_timeout(6500)
    pg.evaluate("""()=>{const els=[...document.querySelectorAll('.md-dialog--full-page button,.md-dialog--full-page i')]
       .filter(e=>/addNew/.test(e.textContent)&&e.offsetParent!==null); if(els.length)els[0].click();}""")
    pg.wait_for_timeout(7000)
    print(f"  [ctx] registration #{reg}; wizard at step {step_of(pg)}", flush=True)

    nxt(pg); pg.wait_for_timeout(6000)
    s=step_of(pg); print("  now at step", s, flush=True)

    # --- Claim|5 : is Notes enforced on step 2? ---
    ndef=pg.evaluate(f"""()=>{{const d={SUB};const n=d.querySelector('#notes');
      return n?{{val:n.value,required:n.required,vis:n.offsetParent!==null,
        label:(n.closest('.md-text-field-container,.md-cell')||{{}}).innerText?.slice(0,40)}}:null;}}""")
    print("  notes field:", ndef, flush=True)
    # make sure it is empty, then try to advance
    pg.evaluate(f"""()=>{{const d={SUB};const n=d.querySelector('#notes');
      if(n){{const s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
      s.call(n,'');n.dispatchEvent(new Event('input',{{bubbles:true}}));}}}}""")
    pg.wait_for_timeout(1200)
    before=step_of(pg)
    r=nxt(pg); pg.wait_for_timeout(5500)
    after=step_of(pg)
    errs=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}}""")
    enforced = (after==before) or any('note' in e.lower() for e in errs)
    rec("Claim|5","PASS" if enforced else "FAIL",
        (f"Notes is enforced: with Notes empty the wizard refuses to advance (stayed on Step {before}; errors {errs})."
         if enforced else
         f"Notes is NOT enforced on this step. With the Notes field empty (id=#notes, required attribute={ndef.get('required') if ndef else 'n/a'}), Next advanced from Step {before} to Step {after} with no validation message. Test case expects the Notes field to validate and block progression."))

    # go back to step 2 if we advanced
    if after!=before:
        pg.evaluate(f"""()=>{{const d={SUB};const b=[...d.querySelectorAll('button')].find(x=>/Previous/i.test(x.textContent));if(b)b.click();}}""")
        pg.wait_for_timeout(5500)
    print("  back at step", step_of(pg), flush=True)

    # --- Claim|6 : can the user type into Notes? ---
    ok=False; got=None
    try:
        ta=pg.locator(".md-dialog:not(.md-dialog--full-page) #notes")
        ta.fill("Regression QA verification note — wizard validated, no claim submitted.")
        pg.wait_for_timeout(1000); got=ta.input_value(); ok=len(got)>0
    except Exception as e: print("   notes err", str(e)[:80], flush=True)
    rec("Claim|6","PASS" if ok else "FAIL", f"Notes field (#notes) accepts typed input — reads '{(got or '')[:60]}'.")

    # --- Claim|7 : Next advances to step 3 ---
    b4=step_of(pg); r3=nxt(pg); pg.wait_for_timeout(6500); s3=step_of(pg)
    rec("Claim|7","PASS" if s3=="3" else "FAIL", f"Next advances the wizard from Step {b4} to Step {s3} ({r3}) — Step 3 is the Claim Receipt / review step.")

    pg.evaluate(f"""()=>{{const d={SUB};const c=[...d.querySelectorAll('button')].find(x=>/Cancel/i.test(x.textContent));if(c)c.click();}}""")
    pg.wait_for_timeout(3000)
    print("  [cleanup] wizard cancelled — no claim created", flush=True)
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
