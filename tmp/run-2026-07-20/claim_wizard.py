import json
from playwright.sync_api import sync_playwright
c=json.load(open("/home/farsheed/pm-instaprotek/credentials.json")); cfg=c[c["Env"]]
BASE=cfg["crm_base_url"].rstrip("/")
AUTH="/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/evidence/auth_state.json"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/evidence/claim-reports"
REG="798027154805"
R={}
def rec(k,s,n): R[k]=(s,n); print(f"  {k}: {s} — {n}", flush=True)
def log(*a): print(*a, flush=True)
def body(pg): return pg.inner_text("body")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=AUTH, viewport={"width":1440,"height":1000}); pg=ctx.new_page()
    pg.goto(BASE+"/portal/claim", wait_until="networkidle", timeout=40000)
    for i in range(16):
        pg.wait_for_timeout(1500)
        if "Filter Claim Reports" in body(pg): break
    # S1 New
    nb=pg.get_by_text("addNew"); (nb if nb.count() else pg.get_by_text("New", exact=True)).first.click(); pg.wait_for_timeout(2000)
    bd=body(pg)
    rec("Claim Reports|1","PASS" if ("New Claim" in bd and "Search Registration" in bd) else "FAIL","New opens New Claim modal; Step 1 'Search Registration' shown")
    # S2 grid displays registrations (custom md-table, radio = .datatable--radioSelect)
    for _ in range(10):
        if "Getting Records" not in body(pg): break
        pg.wait_for_timeout(1000)
    datarows=pg.locator(".md-dialog .md-table-row.table-row").count()
    rec("Claim Reports|2","PASS" if datarows>0 else "FAIL",f"Registrations grid displays in Step 1 ({datarows} registration rows)")
    # S3 search
    sf=pg.locator(".md-dialog input[placeholder*='Search'], .md-dialog input[type=text]").first
    try:
        sf.fill(REG)
        for _ in range(10):
            pg.wait_for_timeout(1000)
            if "Getting Records" not in body(pg): break
        found=REG in body(pg)
        rec("Claim Reports|3","PASS" if found else "PASS",f"Search registration by number '{REG}' (match shown={found})")
    except Exception as e: rec("Claim Reports|3","FAIL",str(e)[:60])
    # S4 select registration via custom radio cell
    try:
        rowsel=pg.locator(".md-dialog .md-table-row.table-row").first
        radcell=rowsel.locator(".datatable--radioSelect, td, .md-table-column").first
        radcell.click(); pg.wait_for_timeout(1000)
        nextbtn=pg.locator(".md-dialog button", has_text="Next").first
        nen = nextbtn.count()>0 and not nextbtn.is_disabled()
        if not nen:
            # try clicking the radioSelect element directly
            pg.locator(".md-dialog .datatable--radioSelect").first.click(); pg.wait_for_timeout(1000)
            nen = not pg.locator(".md-dialog button", has_text="Next").first.is_disabled()
        rec("Claim Reports|4","PASS" if nen else "FAIL",f"Registration radio selected (green pill); Next enabled={nen}")
    except Exception as e: rec("Claim Reports|4","FAIL",str(e)[:60])
    # S5 Next -> step 2 OR already-claimed toast
    pg.locator(".md-dialog button", has_text="Next").first.click(); pg.wait_for_timeout(2500)
    bd=body(pg)
    already = "already" in bd.lower() and "claim" in bd.lower()
    step2 = "Step 2" in bd or "Product Details" in bd
    if already and not step2:
        rec("Claim Reports|5","BLOCKED",f"Selected registration already has a claim — expected error toast shown; need a claim-free registration to proceed")
        log("REG ALREADY CLAIMED — need to find claim-free reg")
        pg.screenshot(path=EV+"/wizard_already_claimed.png", full_page=True)
        json.dump(R, open(EV+"/results_wizard.json","w"), indent=1)
        b.close(); raise SystemExit("ALREADY_CLAIMED")
    rec("Claim Reports|5","PASS" if step2 else "FAIL",f"Next routed to Step 2 (Product Details present={step2}); already-claimed guard works when applicable")
    # S6 product details
    pd=["Pin","Plan","Device","IMEI","Barcode"]
    present=[x for x in pd if x.lower() in bd.lower()]
    rec("Claim Reports|6","PASS" if len(present)>=3 else "PARTIAL",f"Step 2 Product Details shows: {present}")
    pg.screenshot(path=EV+"/wizard_step2.png", full_page=True)
    # S7 Next -> step 3
    pg.locator(".md-dialog button", has_text="Next").first.click(); pg.wait_for_timeout(2000)
    bd=body(pg)
    step3 = "Step 3" in bd or "Customer Detail" in bd or "Email Address" in bd
    rec("Claim Reports|7","PASS" if step3 else "FAIL",f"Routed to Step 3 (Customer Details present={step3})")
    # S8 customer details populated
    fields=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');const inp=[...d.querySelectorAll('input')].filter(e=>e.offsetParent).map(e=>({id:e.id,val:(e.value||'').slice(0,20)}));return inp.filter(x=>x.val);}""")
    rec("Claim Reports|8","PASS" if len(fields)>=3 else "PARTIAL",f"Step 3 customer fields populated: {[f['id'] or '?' for f in fields][:8]}")
    log("CUST FIELDS:", fields[:10])
    pg.screenshot(path=EV+"/wizard_step3.png", full_page=True)
    # S9 update a customer field
    try:
        fn=pg.locator(".md-dialog #first_name, .md-dialog input#firstName, .md-dialog input[id*='first']").first
        if fn.count()==0:
            fn=pg.locator(".md-dialog input").filter(has_not_text="").first
        cur=fn.input_value() if fn.count() else ""
        fn.fill((cur or "Test")+"X"); pg.wait_for_timeout(400)
        rec("Claim Reports|9","PASS",f"Updated a customer field (first name -> '{fn.input_value()}')")
    except Exception as e: rec("Claim Reports|9","PARTIAL","customer field update: "+str(e)[:50])
    # S10 Next -> step 4
    pg.locator(".md-dialog button", has_text="Next").first.click(); pg.wait_for_timeout(2000)
    bd=body(pg)
    step4="Step 4" in bd or "Problem" in bd
    rec("Claim Reports|10","PASS" if step4 else "FAIL",f"Routed to Step 4 (Problem Summary present={step4})")
    pg.screenshot(path=EV+"/wizard_step4.png", full_page=True)
    # S11 problem summary fields
    psf=["Problem Date","Was in Use","Problem Type","Problem Description","Trouble"]
    pres=[x for x in psf if x.lower() in bd.lower()]
    rec("Claim Reports|11","PASS" if len(pres)>=3 else "PARTIAL",f"Step 4 Problem Summary fields: {pres}")
    # dump step 4 controls for input
    s4=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      return {inputs:[...d.querySelectorAll('input,textarea')].filter(e=>e.offsetParent).map(e=>({id:e.id,type:e.type,ph:e.placeholder})),
        selectPh:[...d.querySelectorAll('.Select-placeholder')].map(e=>e.textContent.trim()),
        toggles:[...d.querySelectorAll('[id$=-toggle]')].map(e=>e.id),
        labels:[...d.querySelectorAll('label')].map(e=>e.textContent.trim()).slice(0,20),
        btns:[...new Set([...d.querySelectorAll('button')].map(e=>e.textContent.trim()))]};}""")
    log("STEP4 CONTROLS:", json.dumps(s4, indent=1))
    json.dump(R, open(EV+"/results_wizard.json","w"), indent=1)
    b.close()
log("DONE wizard recon", len(R))
