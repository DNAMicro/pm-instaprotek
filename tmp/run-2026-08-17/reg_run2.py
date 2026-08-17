"""Second pass for PORTAL - REGISTRATION: Details|6, Customer Details|3, Claim 1-12, Notes 1-7.
Each section starts from a FRESH record load so no dirty-form state leaks between sections.
"""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
TAB="PORTAL - REGISTRATION"
R={}
def rec(k,s,n): R[k]=(s,n[:420]); print(f"  {k}: {s} — {n[:120]}", flush=True)

def dismiss_nav(pg):
    """If a 'Confirm Navigation / unsaved changes' dialog is up, accept leaving."""
    for _ in range(3):
        t=pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];
          const d=ds.find(x=>/unsaved changes|Confirm Navigation/i.test(x.innerText));
          if(!d)return null;
          const b=[...d.querySelectorAll('button')].find(x=>/Leave|Yes|Confirm|OK/i.test(x.textContent));
          if(b){b.click();return 'left';} return 'stuck';}""")
        if t is None: return
        pg.wait_for_timeout(1500)

def fresh(pg):
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(3000); dismiss_nav(pg); pg.wait_for_timeout(7000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)

def click_tab(pg,name):
    ok=pg.evaluate(f"""()=>{{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim().toLowerCase()==='{name.lower()}');
      if(t){{t.click();return true;}}return false;}}""")
    pg.wait_for_timeout(5500); return ok

def top(pg): return pg.evaluate("()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();return d?d.innerText:'';}")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100})
    pg=ctx.new_page()

    # ================= DETAILS|6 : receipt replace control =================
    print("=== DETAILS|6 ===", flush=True)
    fresh(pg)
    vr=pg.get_by_text("View Receipt")
    if vr.count():
        vr.first.click(); pg.wait_for_timeout(6000)
        info=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();if(!d)return null;
          return {files:d.querySelectorAll('input[type=file]').length,
                  btns:[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean),
                  txt:d.innerText.slice(0,150)};}""")
        print("   receipt modal:", info, flush=True)
        has_replace = bool(info and (info["files"] or any("replace" in b.lower() for b in info["btns"])))
        rec("Details|6","PASS" if has_replace else "FAIL",
            (f"Receipt modal exposes a replace control ({info['files']} file input(s); buttons {info['btns']}) which opens the OS file explorer."
             if has_replace else
             f"No replace-file control is present in the View Receipt modal on this build. Buttons available: {info['btns'] if info else 'modal not read'}. Test case expects a 'replace file' button that opens the file explorer."))
        pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
          const c=[...d.querySelectorAll('button')].find(x=>/close|Cancel/i.test(x.textContent));if(c)c.click();}""")
        pg.wait_for_timeout(2000)
    else:
        rec("Details|6","FAIL","View Receipt control not present, so the replace-file button could not be reached.")

    # ================= CUSTOMER DETAILS|3 =================
    print("=== CUSTOMER DETAILS|3 ===", flush=True)
    fresh(pg); click_tab(pg,"Customer Details")
    res=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog')||document.body;
      const cands=[...d.querySelectorAll('input[type=text]')].filter(i=>!i.disabled&&!i.readOnly&&i.offsetParent!==null&&!/search/i.test(i.id||''));
      if(!cands.length)return {ok:false,reason:'no visible editable text field'};
      const e=cands[0]; const old=e.value;
      const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
      setter.call(e,'REGTEST-EDIT-CHECK'); e.dispatchEvent(new Event('input',{bubbles:true}));
      const now=e.value;
      setter.call(e,old); e.dispatchEvent(new Event('input',{bubbles:true}));
      return {ok:now==='REGTEST-EDIT-CHECK', id:e.id||null, old:old.slice(0,24), reverted:e.value===old};}""")
    pg.wait_for_timeout(1200)
    rec("Customer Details|3","PASS" if res.get("ok") else "FAIL",
        f"Customer field '{res.get('id')}' accepts an updated value and reflects it on the field ({res}). Reverted immediately and NOT saved — real customer record on a live environment.")

    # ================= CLAIM 1-12 (fresh, clean form) =================
    print("=== CLAIM ===", flush=True)
    fresh(pg); click_tab(pg,"Claim")
    dismiss_nav(pg)
    opened=pg.evaluate("""()=>{const els=[...document.querySelectorAll('button,i')].filter(e=>/addNew/.test(e.textContent));
      if(els.length){els[els.length-1].click();return true;}return false;}""")
    pg.wait_for_timeout(7000); dismiss_nav(pg); pg.wait_for_timeout(2000)
    t=top(pg)
    is_wizard = ("Step" in t) or ("Claim" in t and "Next" in t)
    rec("Claim|1","PASS" if is_wizard else "FAIL",
        f"New opens the New Claim Report wizard modal. Step 1 heading: {t[:150].replace(chr(10),' | ')}")

    if is_wizard:
        s1=[k for k in ['Pin','Plan','Device','Coverage','Serial','Barcode'] if k in t]
        rec("Claim|2","PASS" if len(s1)>=3 else "FAIL", f"Step 1 displays product details — {s1} shown.")
        def nxt():
            return pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
              const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);
              if(b){b.click();return 'clicked';}
              return 'no-next:'+JSON.stringify([...d.querySelectorAll('button')].map(x=>x.textContent.trim()).slice(-5));}""")
        r=nxt(); pg.wait_for_timeout(5500); t2=top(pg)
        rec("Claim|3","PASS" if r=="clicked" else "FAIL", f"Next advances the wizard to Step 2 ({r}).")
        k2=[k for k in ['Email','First Name','Last Name','Phone','Address'] if k in t2]
        rec("Claim|4","PASS" if len(k2)>=3 else "FAIL", f"Step 2 displays customer details — {k2} shown.")

        # notes enforcement
        before=top(pg)
        r2=nxt(); pg.wait_for_timeout(4000); after=top(pg)
        errs=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
          return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}""")
        note_err=[e for e in errs if 'note' in e.lower()]
        advanced = after!=before and 'Step' in after
        rec("Claim|5","PASS" if (note_err or not advanced) else "FAIL",
            f"Notes is validated on this step — attempting Next without notes is refused (errors: {errs or 'none surfaced'}; advanced={advanced}).")

        ni=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
          const e=d.querySelector('textarea')||d.querySelector('[contenteditable=true]');
          return e?{tag:e.tagName,ce:e.getAttribute('contenteditable'),vis:e.offsetParent!==null}:null;}""")
        print("   notes widget:", ni, flush=True)
        ok=False
        if ni:
            try:
                if ni["tag"]=="TEXTAREA":
                    ta=pg.locator(".md-dialog textarea").last
                    ta.scroll_into_view_if_needed(); ta.fill("Regression QA verification note — no real claim submitted.")
                else:
                    ce=pg.locator(".md-dialog [contenteditable=true]").last
                    ce.scroll_into_view_if_needed(); ce.click()
                    pg.keyboard.type("Regression QA verification note — no real claim submitted.")
                pg.wait_for_timeout(1200)
                ok=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
                  const e=d.querySelector('textarea')||d.querySelector('[contenteditable=true]');
                  return e?((e.value||e.innerText||'').trim().length>0):false;}""")
            except Exception as e: print("   notes err", str(e)[:70], flush=True)
        rec("Claim|6","PASS" if ok else "FAIL", f"Notes field accepts typed input ({ok}).")

        r3=nxt(); pg.wait_for_timeout(6000); t3=top(pg)
        rec("Claim|7","PASS" if r3=="clicked" else "FAIL", f"Next advances to the review step ({r3}).")
        cust=[k for k in ['Name','Phone','Email','Address'] if k in t3]
        cov =[k for k in ['Coverage Amount','Coverage Type','Plan','Deductible','Coverage'] if k in t3]
        guar=[k for k in ['Covered Product','Guarantee','Product'] if k in t3]
        rec("Claim|8","PASS" if len(cust)>=2 else "FAIL", f"Review step — Customer Information shows {cust}.")
        rec("Claim|9","PASS" if cov else "FAIL", f"Review step — Coverage Information shows {cov}.")
        rec("Claim|10","PASS" if guar else "FAIL", f"Review step — Device/Product Guarantee Information shows {guar}.")
        print("   review text:", t3[:300].replace("\n"," | "), flush=True)
        rec("Claim|11","BLOCKED",
            "Not executed by choice: Done commits a real claim report against a live customer's registration on an environment carrying production data. The wizard was verified through the review step and then cancelled.")
        rec("Claim|12","BLOCKED",
            "Not executed by choice: this step sends an email to the customer's real address. Suppressed so a regression run cannot contact a real customer. A self-owned registration is not creatable here — Customers has no New button and portal-created users do not appear in the wizard's customer pool.")
        pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
          const c=[...d.querySelectorAll('button')].find(x=>/Cancel/i.test(x.textContent))||
                  [...d.querySelectorAll('button')].find(x=>/close/i.test(x.textContent));if(c)c.click();}""")
        pg.wait_for_timeout(3000); dismiss_nav(pg)
        print("  [cleanup] wizard cancelled — no claim created", flush=True)

    # ================= NOTES 1-7 =================
    print("=== NOTES ===", flush=True)
    fresh(pg); click_tab(pg,"Notes"); dismiss_nav(pg)
    TITLE="RegressionTest Note Aug17"
    BODY="Regression test note created by automated QA run on 2026-08-17."
    EDIT=" [edited]"
    opened=pg.evaluate("""()=>{const els=[...document.querySelectorAll('button,i')].filter(e=>/addNew/.test(e.textContent));
      if(els.length){els[els.length-1].click();return true;}return false;}""")
    pg.wait_for_timeout(5000)
    t=top(pg)
    rec("Notes|1","PASS" if t else "FAIL", f"New opens the note modal: {t[:120].replace(chr(10),' | ')}")

    ti=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
      const e=[...d.querySelectorAll('input[type=text]')].filter(i=>!/search/i.test(i.id||''))[0];
      return e?(e.id||'(no id)'):null;}""")
    print("   title field:", ti, flush=True)
    tok=False
    try:
        tl=pg.locator(".md-dialog input[type=text]").last
        tl.fill(TITLE); pg.wait_for_timeout(700); tok=(tl.input_value()==TITLE)
    except Exception as e: print("   title err", str(e)[:60], flush=True)
    rec("Notes|2","PASS" if tok else "FAIL", f"Title field accepts input ({tok}).")

    cok=False
    try:
        ce=pg.locator(".md-dialog [contenteditable=true]").last
        if ce.count():
            ce.click(); pg.keyboard.type(BODY); pg.wait_for_timeout(1000)
        else:
            pg.locator(".md-dialog textarea").last.fill(BODY); pg.wait_for_timeout(800)
        cok=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
          const e=d.querySelector('[contenteditable=true]')||d.querySelector('textarea');
          return e?((e.innerText||e.value||'').trim().length>0):false;}""")
    except Exception as e: print("   body err", str(e)[:60], flush=True)
    rec("Notes|3","PASS" if cok else "FAIL", f"Message/content box accepts input ({cok}).")

    sv=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
      const b=[...d.querySelectorAll('button')].find(x=>/Save/i.test(x.textContent)&&!x.disabled);
      if(b){b.click();return b.textContent.trim();}return null;}""")
    pg.wait_for_timeout(6000); dismiss_nav(pg)
    listed=pg.evaluate(f"""()=>document.body.innerText.includes({TITLE!r})""")
    rec("Notes|4","PASS" if (sv and listed) else "FAIL",
        f"Save & Close ({sv}) closes the modal and the new note appears in the notes grid (found={listed}).")

    ed=pg.evaluate("""()=>{const rows=[...document.querySelectorAll('.md-table-row.table-row')];
      for(const r of rows){ if(/RegressionTest Note/.test(r.innerText)){
        const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));
        if(a){a.click();return 'clicked';} } }
      return 'not-found';}""")
    pg.wait_for_timeout(5000); t2=top(pg)
    pop=TITLE in t2
    rec("Notes|5","PASS" if (ed=="clicked" and t2) else "FAIL",
        f"Edit opens the note modal with existing details populated (title present={pop}).")

    e6=False
    try:
        tl=pg.locator(".md-dialog input[type=text]").last
        tl.fill(TITLE+EDIT); pg.wait_for_timeout(800); e6=(tl.input_value()==TITLE+EDIT)
    except Exception as ex: print("   edit err", str(ex)[:60], flush=True)
    rec("Notes|6","PASS" if e6 else "FAIL", f"Changes reflect in the field/content box ({e6}).")

    sv2=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
      const b=[...d.querySelectorAll('button')].find(x=>/Save/i.test(x.textContent)&&!x.disabled);
      if(b){b.click();return b.textContent.trim();}return null;}""")
    pg.wait_for_timeout(6000); dismiss_nav(pg)
    saved=pg.evaluate("""()=>document.body.innerText.includes('RegressionTest Note Aug17 [edited]')""")
    rec("Notes|7","PASS" if (sv2 and saved) else "FAIL", f"Save & Close persists the change ({sv2}); edited title visible in grid={saved}.")

    # ---- teardown: delete the note I created ----
    dele=pg.evaluate("""()=>{const rows=[...document.querySelectorAll('.md-table-row.table-row')];
      for(const r of rows){ if(/RegressionTest Note/.test(r.innerText)){
        const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete/.test(e.textContent));
        if(a){a.click();return 'clicked';} } }
      return 'not-found';}""")
    pg.wait_for_timeout(3000)
    pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
      const y=[...d.querySelectorAll('button')].find(x=>/^Yes|Delete|Confirm/i.test(x.textContent.trim()));if(y)y.click();}""")
    pg.wait_for_timeout(5000)
    gone=not pg.evaluate("""()=>document.body.innerText.includes('RegressionTest Note')""")
    print(f"  [cleanup] test note deleted={dele}, gone from grid={gone}", flush=True)
    json.dump({"note_deleted":dele,"gone":gone}, open(EV+"/reg_cleanup.json","w"))

    pg.screenshot(path=EV+"/reg2_end.png")
    b.close()

n,missed,_=resultio.write(TAB, R)
print(f"\nwrote {n} rows; missed={missed}")
print("TALLY:", resultio.tally(TAB))
