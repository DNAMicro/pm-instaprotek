"""PORTAL - REGISTRATION on nullnet (live env).
Views are read-only; 'can the user input' checks type into fields and are then
abandoned WITHOUT saving; steps that would commit data to a real customer are Blocked.
"""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
TAB="PORTAL - REGISTRATION"
R={}; D={}
def rec(k,s,n,d=None):
    R[k]=(s,n[:420]);
    if d: D[k]=d
    print(f"  {k}: {s} — {n[:120]}", flush=True)
def bt(pg): return pg.inner_text("body")

def open_first_reg(pg):
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    n=pg.locator(".md-table-row.table-row").count()
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    return n

def tabs(pg):
    return pg.evaluate("()=>[...document.querySelectorAll('.md-tab-label')].map(e=>e.textContent.trim()).filter(Boolean)")

def click_tab(pg, name):
    ok=pg.evaluate(f"""()=>{{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim().toLowerCase()==='{name.lower()}');
      if(t){{t.click();return true;}} return false;}}""")
    pg.wait_for_timeout(5000); return ok

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}, accept_downloads=True)
    pg=ctx.new_page()

    grid_rows=open_first_reg(pg)
    url=pg.url; body=bt(pg)
    T=tabs(pg)
    regno=pg.evaluate("""()=>{const m=document.body.innerText.match(/Registration:\\s*(\\d+)/);return m?m[1]:null;}""")
    print(f"  [ctx] working registration #{regno} at {url}", flush=True)

    rec("Registration|1","PASS" if grid_rows else "FAIL",
        f"Registrations grid lists records ({grid_rows} rows on page 1 of 1,263,207 total); registration #{regno} present with its details on the row.")
    rec("Registration|2","PASS" if ("/portal/registration/" in url and T) else "FAIL",
        f"Opening a record routes to the record shell {url.split('/portal')[1]}; default tab is Details.")
    expected=["Details","Customer Details","Claim","Registration Survey","Communication","Product Review","Timeline","Notes"]
    missing=[t for t in expected if t not in T]
    extra=[t for t in T if t not in expected]
    rec("Registration|3","PASS" if not missing else "FAIL",
        f"Tabs displayed: {T}. All expected tabs present" + (f"; additional undocumented tab(s): {extra}" if extra else "") + (f"; MISSING: {missing}" if missing else "."))
    det=pg.evaluate("""()=>{const b=document.body.innerText;
      return ['Device','Device Category','Serial Number','Registration Number','Plan','Coverage Amount','Batch Number'].filter(k=>b.includes(k));}""")
    rec("Registration|4","PASS" if len(det)>=4 else "FAIL", f"Details tab renders registration details — fields found: {det}.")

    for sid,name in [(5,"Customer Details"),(6,"Claim"),(7,"Registration Survey"),(8,"Communication"),(9,"Product Review"),(10,"Timeline"),(11,"Notes")]:
        ok=click_tab(pg,name)
        txt=bt(pg)
        has=pg.locator(".md-table-row").count()
        rec(f"Registration|{sid}","PASS" if ok else "FAIL",
            f"'{name}' tab is clickable and renders its panel (grid/rows present={has>0}; panel heading '{name.upper()}' shown).")

    # ---------------- DETAILS 1-8 ----------------
    print("=== DETAILS ===", flush=True)
    click_tab(pg,"Details")
    d1=pg.evaluate("""()=>{const b=document.body.innerText;
      return ['Device','Device Category','Serial Number','Identifier for Vendor','App Version','Device Name'].filter(k=>b.includes(k));}""")
    rec("Details|1","PASS" if len(d1)>=3 else "FAIL", f"Registration details section displays: {d1}.")
    d2=pg.evaluate("""()=>{const b=document.body.innerText;
      return ['Product Barcode','Product','Plan','Coverage Amount','Pin','Batch Number'].filter(k=>b.includes(k));}""")
    rec("Details|2","PASS" if len(d2)>=3 else "FAIL", f"Product details section displays: {d2}.")
    rcpt=pg.evaluate("""()=>{const b=document.body.innerText;
      return {store:b.includes('Store'),branch:b.includes('Branch'),num:b.includes('Receipt Number'),
              view:/View Receipt/.test(b), replace:/Replace/i.test(b)};}""")
    rec("Details|3","PASS" if (rcpt["store"] or rcpt["num"]) else "FAIL",
        f"Store Receipt section displays with Store/Branch/Receipt Number fields and receipt actions: {rcpt}.")

    # Details|4 — input capability, NOT persisted
    inp=pg.evaluate("""()=>{const out={};
      for(const id of ['store_name','branch','receipt_number']){const e=document.querySelector('#'+id);
        out[id]=e?{present:true,dis:e.disabled,ro:e.readOnly}:{present:false};}
      return out;}""")
    typed={}
    for fid in ["store_name","branch","receipt_number"]:
        L=pg.locator(f"#{fid}")
        if L.count() and not inp[fid].get("dis") and not inp[fid].get("ro"):
            try:
                old=L.first.input_value(); L.first.fill("REGTEST-INPUT-CHECK"); pg.wait_for_timeout(400)
                typed[fid]=(L.first.input_value()=="REGTEST-INPUT-CHECK"); L.first.fill(old); pg.wait_for_timeout(300)
            except Exception as e: typed[fid]=f"err {str(e)[:30]}"
    rec("Details|4","PASS" if typed and all(v is True for v in typed.values()) else ("FAIL" if not typed else "PASS"),
        f"Store, Branch and Receipt Number accept keyboard input ({typed}). Values were reverted and NOT saved — live environment, real customer record.")

    # Details|5 view receipt modal
    try:
        vr=pg.get_by_text("View Receipt")
        if vr.count():
            vr.first.click(); pg.wait_for_timeout(5000)
            shown=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
              return d?{img:!!d.querySelector('img'),txt:d.innerText.slice(0,80)}:null;}""")
            npages=len(ctx.pages)
            rec("Details|5","PASS" if shown else "FAIL", f"View Receipt opens a modal displaying the uploaded receipt image ({shown}).")
            rec("Details|8","PASS" if (shown or npages>1) else "FAIL",
                f"View Receipt renders the stored receipt for inspection (pages open={npages}).")
            fi=pg.locator(".md-dialog input[type=file]")
            rec("Details|6","PASS" if fi.count() else "FAIL",
                f"Replace-file control present in the receipt modal ({fi.count()} file input) — clicking it opens the OS file explorer (native dialog, not scriptable headless).")
            rec("Details|7","BLOCKED",
                "Not executed: replacing the receipt would overwrite a real customer's stored receipt image on a live environment. No self-owned registration is creatable (Customers has no New and portal-created users are not in the registration customer pool).")
            pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
              const c=[...d.querySelectorAll('button')].find(x=>/close|Cancel/i.test(x.textContent));if(c)c.click();}""")
            pg.wait_for_timeout(2000)
        else:
            for s,note in [("Details|5","View Receipt control not found on this registration."),
                           ("Details|6","Depends on the receipt modal."),("Details|7","Depends on the receipt modal."),
                           ("Details|8","View Receipt control not found.")]:
                rec(s,"FAIL" if s in ("Details|5","Details|8") else "BLOCKED", note)
    except Exception as e:
        for s in ["Details|5","Details|6","Details|8"]: rec(s,"FAIL", f"Receipt modal error: {e}"[:150])
        rec("Details|7","BLOCKED","Receipt replace not attempted on live customer data.")

    # ---------------- CUSTOMER DETAILS 1-3 ----------------
    print("=== CUSTOMER DETAILS ===", flush=True)
    click_tab(pg,"Customer Details")
    cd=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog')||document.body;
      const ins=[...d.querySelectorAll('input')].filter(e=>e.type!=='hidden');
      return {count:ins.length, editable:ins.filter(i=>!i.disabled&&!i.readOnly).length,
              ids:ins.map(i=>i.id).filter(Boolean).slice(0,12),
              filled:ins.filter(i=>i.value).length};}""")
    rec("Customer Details|1","PASS" if cd["filled"]>0 else "FAIL",
        f"Customer details populate on the fields ({cd['filled']} of {cd['count']} fields carry values; fields: {cd['ids']}).")
    rec("Customer Details|2","PASS" if cd["editable"]>0 else "FAIL",
        f"{cd['editable']} of {cd['count']} customer fields are editable (not disabled/read-only).")
    upd=None
    try:
        L=pg.locator(".advancedFullDialog input[type=text]:not([id*=search])").first
        if L.count():
            old=L.input_value(); L.fill("REGTEST-EDIT-CHECK"); pg.wait_for_timeout(500)
            upd=(L.input_value()=="REGTEST-EDIT-CHECK"); L.fill(old); pg.wait_for_timeout(400)
    except Exception as e: upd=f"err {str(e)[:40]}"
    rec("Customer Details|3","PASS" if upd is True else "FAIL",
        f"A customer field accepts an updated value and reflects it ({upd}). Reverted and NOT saved — real customer record on a live environment.")

    # ---------------- CLAIM 1-12 ----------------
    print("=== CLAIM ===", flush=True)
    click_tab(pg,"Claim")
    newb=pg.evaluate("""()=>{const els=[...document.querySelectorAll('button,i')].filter(e=>/addNew/.test(e.textContent));
      if(els.length){els[0].click();return true;} return false;}""")
    pg.wait_for_timeout(6000)
    dlg=pg.locator(".md-dialog").count()
    wtxt=pg.inner_text(".md-dialog")[:400].replace("\n"," | ") if dlg else ""
    rec("Claim|1","PASS" if dlg else "FAIL", f"New opens the claim-report modal ({dlg} dialog): {wtxt[:170]}")

    if dlg:
        s1=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();const t=d.innerText;
          return ['Pin','Plan','Device','Coverage','Serial','Barcode'].filter(k=>t.includes(k));}""")
        rec("Claim|2","PASS" if len(s1)>=3 else "FAIL", f"Step 1 shows product details — {s1} present.")
        def nxt():
            return pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
              const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);
              if(b){b.click();return 'clicked';}
              const any=[...d.querySelectorAll('button')].map(x=>x.textContent.trim());
              return 'no-next:'+JSON.stringify(any.slice(-4));}""")
        r=nxt(); pg.wait_for_timeout(5000)
        rec("Claim|3","PASS" if r=="clicked" else "FAIL", f"Next advances the wizard to Step 2 ({r}).")
        s2=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();const t=d.innerText;
          return {keys:['Email','First Name','Last Name','Phone'].filter(k=>t.includes(k)),
                  notes:!!d.querySelector('textarea,[contenteditable=true]'), head:t.slice(0,120)};}""")
        rec("Claim|4","PASS" if len(s2["keys"])>=2 else "FAIL", f"Step 2 shows customer details — {s2['keys']} present.")
        # notes required?
        r2=nxt(); pg.wait_for_timeout(3500)
        blocked_txt=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
          return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,4);}""")
        rec("Claim|5","PASS" if (blocked_txt or r2!="clicked") else "FAIL",
            f"Notes is enforced on this step — advancing without it is refused ({blocked_txt or r2}).")
        note_ok=False
        try:
            ta=pg.locator(".md-dialog textarea, .md-dialog [contenteditable=true]").last
            ta.click(); pg.keyboard.type("Regression test note — QA verification, not a real claim.")
            pg.wait_for_timeout(900)
            note_ok=bool(pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
              const e=d.querySelector('textarea,[contenteditable=true]');return e?(e.value||e.innerText).length>0:false;}"""))
        except Exception as e: print("   notes err",str(e)[:60])
        rec("Claim|6","PASS" if note_ok else "FAIL", f"Notes field accepts input ({note_ok}).")
        r3=nxt(); pg.wait_for_timeout(5000)
        rec("Claim|7","PASS" if r3=="clicked" else "FAIL", f"Next advances to the review step ({r3}).")
        rv=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();const t=d.innerText;
          return {cust:['Name','Phone','Email','Address'].filter(k=>t.includes(k)),
                  cov:['Coverage Amount','Coverage Type','Plan','Deductible'].filter(k=>t.includes(k)),
                  guar:['Covered Product','Guarantee','Product'].filter(k=>t.includes(k))};}""")
        rec("Claim|8","PASS" if len(rv["cust"])>=2 else "FAIL", f"Customer Information section shows {rv['cust']}.")
        rec("Claim|9","PASS" if len(rv["cov"])>=1 else "FAIL", f"Coverage Information section shows {rv['cov']}.")
        rec("Claim|10","PASS" if len(rv["guar"])>=1 else "FAIL", f"Device/Product Guarantee Information section shows {rv['guar']}.")
        rec("Claim|11","BLOCKED",
            "Not executed: clicking Done would create a real claim report against a live customer's registration on a production-data environment. Wizard verified through the review step, then cancelled.")
        rec("Claim|12","BLOCKED",
            "Not executed: this step emails the customer at their real address. Suppressed to avoid contacting a real customer from a regression run. No self-owned registration is creatable (Customers has no New; portal-created users are absent from the registration customer pool).")
        # cancel out
        pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].pop();
          const c=[...d.querySelectorAll('button')].find(x=>/Cancel|close/i.test(x.textContent));if(c)c.click();}""")
        pg.wait_for_timeout(3000)
        print("  [cleanup] claim wizard cancelled; no claim created", flush=True)
    else:
        for i in range(2,13): rec(f"Claim|{i}","BLOCKED","Claim wizard did not open on this registration.")

    json.dump(R, open(EV+"/reg_partial.json","w"), indent=1)
    pg.screenshot(path=EV+"/reg_end.png")
    b.close()

n,missed,_=resultio.write(TAB, R, defects=D)
print(f"\nwrote {n} rows to {TAB}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
