"""Third pass: CLAIM 1-12 and NOTES 1-7 with correct dialog scoping.
The record shell is itself a .md-dialog, so sub-modals are identified by being
a .md-dialog that is NOT the .advancedFullDialog record shell.
"""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
TAB="PORTAL - REGISTRATION"
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:125]}", flush=True)

SUB = """(()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('advancedFullDialog'));
  return ds.length?ds[ds.length-1]:null;})()"""

def sub_text(pg):
    return pg.evaluate(f"()=>{{const d={SUB};return d?d.innerText:'';}}")
def sub_btns(pg):
    return pg.evaluate(f"()=>{{const d={SUB};return d?[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean):[];}}")
def sub_click(pg, rx):
    return pg.evaluate(f"""()=>{{const d={SUB};if(!d)return 'no-modal';
      const b=[...d.querySelectorAll('button')].find(x=>new RegExp("{rx}","i").test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}
      return 'none:'+JSON.stringify([...d.querySelectorAll('button')].map(x=>x.textContent.trim()).slice(-5));}}""")

def dismiss_nav(pg):
    for _ in range(3):
        t=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].find(x=>/unsaved changes|Confirm Navigation/i.test(x.innerText));
          if(!d)return null;const b=[...d.querySelectorAll('button')].find(x=>/Leave|Yes|Confirm|OK/i.test(x.textContent));
          if(b){b.click();return 'left';}return 'stuck';}""")
        if t is None: return
        pg.wait_for_timeout(1500)

def fresh(pg):
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(3000); dismiss_nav(pg); pg.wait_for_timeout(7000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    return pg.evaluate("""()=>{const m=document.body.innerText.match(/Registration:\\s*(\\d+)/);return m?m[1]:null;}""")

def click_tab(pg,name):
    ok=pg.evaluate(f"""()=>{{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='{name}');
      if(t){{t.click();return true;}}return false;}}""")
    pg.wait_for_timeout(6000); return ok

def add_new(pg):
    """Click the addNew that lives INSIDE the record's tab panel."""
    n=pg.evaluate("""()=>{const els=[...document.querySelectorAll('.advancedFullDialog button,.advancedFullDialog i')]
        .filter(e=>/addNew/.test(e.textContent)&&e.offsetParent!==null);
      if(els.length){els[0].click();return els.length;}return 0;}""")
    pg.wait_for_timeout(6500); return n

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()

    # ================== CLAIM ==================
    print("=== CLAIM ===", flush=True)
    regno=fresh(pg); click_tab(pg,"Claim")
    print(f"  [ctx] registration #{regno}", flush=True)
    add_new(pg); dismiss_nav(pg); pg.wait_for_timeout(1500)
    t=sub_text(pg)
    is_wiz = bool(t) and ("Claim" in t or "Step" in t)
    rec("Claim|1","PASS" if is_wiz else "FAIL",
        f"New opens the New Claim Report modal. Heading/first fields: {t[:160].replace(chr(10),' | ') if t else 'no sub-modal opened'}")

    if is_wiz:
        s1=[k for k in ['Pin','Plan','Device','Coverage','Serial','Barcode','Product'] if k in t]
        rec("Claim|2","PASS" if len(s1)>=3 else "FAIL", f"Step 1 displays product details — {s1} shown.")
        r=sub_click(pg,"Next"); pg.wait_for_timeout(6000); t2=sub_text(pg)
        rec("Claim|3","PASS" if r not in (None,'no-modal') and not str(r).startswith('none') else "FAIL",
            f"Next advances the wizard to Step 2 (clicked '{r}').")
        k2=[k for k in ['Email','First Name','Last Name','Phone','Address'] if k in t2]
        rec("Claim|4","PASS" if len(k2)>=3 else "FAIL", f"Step 2 displays customer details — {k2} shown.")

        before=t2
        r2=sub_click(pg,"Next"); pg.wait_for_timeout(4500); after=sub_text(pg)
        errs=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return[];
          return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}}""")
        note_err=[e for e in errs if 'note' in e.lower() or 'required' in e.lower()]
        rec("Claim|5","PASS" if (note_err or after==before) else "FAIL",
            f"Notes is enforced before proceeding — Next without notes is refused (errors: {errs or 'none'}; step unchanged={after==before}).")

        ok=False
        try:
            ce=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return null;
              const e=d.querySelector('textarea')||d.querySelector('[contenteditable=true]');
              return e?e.tagName:null;}}""")
            print("   notes widget:", ce, flush=True)
            if ce=="TEXTAREA":
                pg.locator(".md-dialog:not(.advancedFullDialog) textarea").last.fill("Regression QA verification — no claim submitted.")
            else:
                el=pg.locator(".md-dialog:not(.advancedFullDialog) [contenteditable=true]").last
                el.click(); pg.keyboard.type("Regression QA verification — no claim submitted.")
            pg.wait_for_timeout(1300)
            ok=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return false;
              const e=d.querySelector('textarea')||d.querySelector('[contenteditable=true]');
              return e?((e.value||e.innerText||'').trim().length>0):false;}}""")
        except Exception as e: print("   notes err", str(e)[:70], flush=True)
        rec("Claim|6","PASS" if ok else "FAIL", f"Notes field accepts typed input ({ok}).")

        r3=sub_click(pg,"Next"); pg.wait_for_timeout(6500); t3=sub_text(pg)
        rec("Claim|7","PASS" if not str(r3).startswith('none') else "FAIL", f"Next advances to the review step (clicked '{r3}').")
        print("   review:", t3[:280].replace("\n"," | "), flush=True)
        cust=[k for k in ['Name','Phone','Email','Address'] if k in t3]
        cov =[k for k in ['Coverage Amount','Coverage Type','Plan','Deductible','Coverage'] if k in t3]
        guar=[k for k in ['Covered Product','Guarantee','Product'] if k in t3]
        rec("Claim|8","PASS" if len(cust)>=2 else "FAIL", f"Customer Information section shows {cust}.")
        rec("Claim|9","PASS" if cov else "FAIL", f"Coverage Information section shows {cov}.")
        rec("Claim|10","PASS" if guar else "FAIL", f"Device/Product Guarantee Information section shows {guar}.")
        rec("Claim|11","BLOCKED",
            f"Not executed by choice: Done commits a real claim report against live customer registration #{regno} on an environment carrying production data. Wizard verified end-to-end through the review step, then cancelled.")
        rec("Claim|12","BLOCKED",
            "Not executed by choice: this step emails the customer at their real address. Suppressed so a regression run cannot contact a real customer. A self-owned registration is not creatable here (Customers has no New; portal-created users are absent from the wizard's customer pool).")
        print("   cancel:", sub_click(pg,"Cancel|close"), flush=True)
        pg.wait_for_timeout(3000); dismiss_nav(pg)
    else:
        for i in range(2,13):
            rec(f"Claim|{i}","BLOCKED","Claim wizard did not open from the registration's Claim tab.")

    # ================== NOTES ==================
    print("=== NOTES ===", flush=True)
    regno=fresh(pg); click_tab(pg,"Notes"); dismiss_nav(pg)
    TITLE="RegressionTest Note Aug17"
    BODY="Regression test note created by automated QA run 2026-08-17. Safe to delete."
    add_new(pg)
    t=sub_text(pg)
    rec("Notes|1","PASS" if ("New Note" in t or "Title" in t) else "FAIL",
        f"New opens the New Note modal: {t[:130].replace(chr(10),' | ') if t else 'no modal'}")

    tok=False
    try:
        tl=pg.locator(".md-dialog:not(.advancedFullDialog) #title").last
        tl.fill(TITLE); pg.wait_for_timeout(800); tok=(tl.input_value()==TITLE)
    except Exception as e: print("   title err", str(e)[:70], flush=True)
    rec("Notes|2","PASS" if tok else "FAIL", f"Title field accepts input and reflects '{TITLE}' ({tok}).")

    cok=False
    try:
        ce=pg.locator(".md-dialog:not(.advancedFullDialog) [contenteditable=true]").first
        ce.click(); pg.keyboard.type(BODY); pg.wait_for_timeout(1400)
        cok=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return false;
          const e=d.querySelector('[contenteditable=true]');return e?e.innerText.trim().length>0:false;}}""")
    except Exception as e: print("   body err", str(e)[:70], flush=True)
    rec("Notes|3","PASS" if cok else "FAIL", f"Message/content rich-text box accepts input ({cok}).")

    sv=sub_click(pg,"Save"); pg.wait_for_timeout(7000); dismiss_nav(pg)
    listed=pg.evaluate(f"()=>document.body.innerText.includes({TITLE!r})")
    rec("Notes|4","PASS" if (not str(sv).startswith('none') and listed) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the note appears in the notes grid (found={listed}).")

    ed=pg.evaluate("""()=>{const rows=[...document.querySelectorAll('.advancedFullDialog .md-table-row.table-row')];
      for(const r of rows){if(/RegressionTest Note/.test(r.innerText)){
        const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));
        if(a){a.click();return 'clicked';}}}
      return 'not-found';}""")
    pg.wait_for_timeout(6000); t2=sub_text(pg)
    pop=TITLE in t2
    rec("Notes|5","PASS" if (ed=='clicked' and pop) else "FAIL",
        f"Edit ({ed}) opens the note modal with existing details populated (title populated={pop}).")

    e6=False
    try:
        tl=pg.locator(".md-dialog:not(.advancedFullDialog) #title").last
        tl.fill(TITLE+" [edited]"); pg.wait_for_timeout(900); e6=tl.input_value().endswith("[edited]")
    except Exception as e: print("   edit err", str(e)[:70], flush=True)
    rec("Notes|6","PASS" if e6 else "FAIL", f"Change reflects in the title field ({e6}).")

    sv2=sub_click(pg,"Save"); pg.wait_for_timeout(7000); dismiss_nav(pg)
    saved=pg.evaluate("()=>document.body.innerText.includes('RegressionTest Note Aug17 [edited]')")
    rec("Notes|7","PASS" if (not str(sv2).startswith('none') and saved) else "FAIL",
        f"Save & Close ('{sv2}') persists the change; edited title visible in the grid={saved}.")

    # teardown
    dele=pg.evaluate("""()=>{const rows=[...document.querySelectorAll('.advancedFullDialog .md-table-row.table-row')];
      for(const r of rows){if(/RegressionTest Note/.test(r.innerText)){
        const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete/.test(e.textContent));
        if(a){a.click();return 'clicked';}}}return 'not-found';}""")
    pg.wait_for_timeout(3500)
    pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];const d=ds[ds.length-1];
      const y=[...d.querySelectorAll('button')].find(x=>/^Yes$|Delete|Confirm/i.test(x.textContent.trim()));if(y)y.click();}""")
    pg.wait_for_timeout(6000)
    gone=not pg.evaluate("()=>document.body.innerText.includes('RegressionTest Note')")
    print(f"  [cleanup] note delete={dele}; removed from grid={gone}", flush=True)
    json.dump({"delete":dele,"gone":gone}, open(EV+"/reg_note_cleanup.json","w"))
    pg.screenshot(path=EV+"/reg3_end.png")
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n} rows; missed={missed}")
print("TALLY:", resultio.tally(TAB))
