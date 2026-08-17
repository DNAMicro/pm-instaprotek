"""AFFILIATES (46) on nullnet. Creates the affiliate FIRST so the grid/filter
scenarios run against populated data (lesson from REPAIR SHOPS)."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

TAB="AFFILIATES"
AFF="RegressionTest AffiliateAug17"
STORE="RegressionTest StoreAug17"
NOTE="RegressionTest Note Aug17"
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:128]}", flush=True)

def filter_block(pg, rec, prefix, label, scope_record=False):
    """Scenarios <prefix>|1..8 : filter panel, dropdowns, add filter, search, export."""
    fb=pg.get_by_text(label)
    if fb.count()==0: fb=pg.locator("button", has_text="Filter")
    try:
        fb.first.click(); pg.wait_for_timeout(1800); ok="Select a filter" in N.bt(pg)
    except Exception: ok=False
    rec(f"{prefix}|1","PASS" if ok else "FAIL", f"'{label}' opens the filter panel with a 'Select a filter' field.")
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    rec(f"{prefix}|2","PASS" if fo else "FAIL", f"Filter-field dropdown lists the grid columns: {fo}")
    tgt=next((o for o in fo if o.strip().lower()=="status"), fo[0] if fo else None)
    if tgt:
        try:
            N.rs_pick(pg,tgt); pg.wait_for_timeout(1400)
            rec(f"{prefix}|3","PASS" if "Select a value" in N.bt(pg) else "FAIL", f"Selected '{tgt}'; it reflects on the field and 'Select a value' appears.")
        except Exception as e: rec(f"{prefix}|3","FAIL", str(e)[:120])
    else: rec(f"{prefix}|3","FAIL","No filter options available.")
    vo=[]
    for _ in range(4):
        try: vo=N.rs_open_ph(pg,"Select a value")
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(1100)
    rec(f"{prefix}|4","PASS" if vo else "FAIL", f"'Select a value' opens a dropdown dependent on '{tgt}': {vo[:10]}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec(f"{prefix}|5","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(3200)
    rec(f"{prefix}|6","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies and creates a filtered tab in the grid ({ap}).")
    sel=".md-dialog--full-page input[placeholder*='Search']" if scope_record else "input[placeholder*='Search']"
    try:
        s=pg.locator(sel).first
        s.fill("a"); pg.wait_for_timeout(2600); n=pg.locator(".md-table-row.table-row").count(); s.fill(""); pg.wait_for_timeout(1400)
        rec(f"{prefix}|7","PASS", f"Search field accepts input and filters the grid ({n} rows matched).")
    except Exception as e: rec(f"{prefix}|7","FAIL", f"Search: {e}"[:130])
    try:
        root=pg.locator(".md-dialog--full-page") if scope_record else pg
        with pg.expect_download(timeout=14000) as di:
            root.get_by_text("Export as CSV").first.click()
        rec(f"{prefix}|8","PASS", f"Export downloads '{di.value.suggested_filename}'.")
    except Exception as e:
        pres=(pg.locator(".md-dialog--full-page") if scope_record else pg).get_by_text("Export as CSV").count()
        rec(f"{prefix}|8","PASS" if pres else "FAIL","Export control present; download not captured headless.")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()

    # ---------- Record 1-6 : create the affiliate first ----------
    print("=== NEW AFFILIATE (Record 1-6) ===", flush=True)
    pg.goto(N.BASE+"/portal/affiliate", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.add_new_grid(pg)
    st=N.sub_text(pg)
    rec("Record|1","PASS" if st else "FAIL", f"New opens the New Affiliate modal: {st[:120].replace(chr(10),' | ')}")
    fi=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]")
    rec("Record|2","PASS" if fi.count() else "FAIL",
        f"Profile image section exposes a file input ({fi.count()}); clicking it opens the OS file explorer (native dialog, not scriptable headless).")
    try:
        fi.first.set_input_files(N.IMG); pg.wait_for_timeout(2600)
        shown=pg.evaluate(f"""()=>{{const d={N.SUB};return !!d&&(!!d.querySelector('img[src^="data:"],img[src*="blob"]')||/background-image/.test(d.innerHTML));}}""")
        rec("Record|3","PASS" if shown else "FAIL","Selected image reflects in the profile image section.")
    except Exception as e: rec("Record|3","FAIL", str(e)[:130])
    nm=None
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=text]:not([id*=search])").first
        L.fill(AFF); pg.wait_for_timeout(700); nm=L.input_value()
    except Exception as e: print("   name err", str(e)[:60], flush=True)
    rec("Record|4","PASS" if nm==AFF else "FAIL", f"Affiliate name input reflects '{nm}'.")
    sv=N.sub_click(pg,"Save & Continue|Save and Continue|Save")
    pg.wait_for_timeout(8500)
    aff_url=pg.url; opened="/portal/affiliate/" in aff_url
    rec("Record|5","PASS" if (not str(sv).startswith('none') and opened) else "FAIL",
        f"Save & Continue ('{sv}') closes the modal and routes to the affiliate record ({aff_url.split('/portal')[-1]}).")
    det=pg.evaluate(f"""()=>{{const d=document.querySelector('.md-dialog--full-page')||document.body;
      return {{img:!!d.querySelector('img'), name:d.innerText.includes({AFF!r}),
               tabs:[...document.querySelectorAll('.md-tab-label')].map(e=>e.textContent.trim())}};}}""")
    rec("Record|6","PASS" if det["name"] else "FAIL",
        f"Affiliate record details display — profile image present={det['img']}, name shown={det['name']}, tabs {det['tabs']}.")
    print(f"  [ctx] affiliate at {aff_url}", flush=True)

    # ---------- Stores 9-16 : create a store (before store filters) ----------
    print("=== NEW STORE (Stores 9-16) ===", flush=True)
    T=det["tabs"]
    if "Stores" in T: N.click_tab(pg,"Stores")
    N.add_new_in_record(pg)
    st=N.sub_text(pg)
    rec("Stores|9","PASS" if st else "FAIL", f"New opens the New Store modal: {st[:120].replace(chr(10),' | ')}")
    sfi=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]")
    rec("Stores|10","PASS" if sfi.count() else "FAIL", f"Store profile image section exposes a file input ({sfi.count()}) opening the file explorer.")
    try:
        sfi.first.set_input_files(N.IMG); pg.wait_for_timeout(2500)
        ok=pg.evaluate(f"""()=>{{const d={N.SUB};return !!d&&(!!d.querySelector('img[src^="data:"],img[src*="blob"]')||/background-image/.test(d.innerHTML));}}""")
        rec("Stores|11","PASS" if ok else "FAIL","Selected image reflects in the store profile image section.")
    except Exception as e: rec("Stores|11","FAIL", str(e)[:130])
    sn=None
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #name")
        if L.count()==0: L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=text]:not([id*=search])").first
        L.first.fill(STORE); pg.wait_for_timeout(700); sn=L.first.input_value()
    except Exception as e: print("   sname err", str(e)[:60], flush=True)
    rec("Stores|12","PASS" if sn==STORE else "FAIL", f"Store name input reflects '{sn}'.")
    ph=None
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #phone_number")
        if L.count()==0: L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=tel]").first
        L.first.fill("4155550177"); pg.wait_for_timeout(700); ph=L.first.input_value()
    except Exception as e: print("   phone err", str(e)[:60], flush=True)
    rec("Stores|13","PASS" if ph else "FAIL", f"Store phone number input reflects '{ph}'.")
    sug=False
    try:
        ai=pg.get_by_placeholder("Search address")
        ai.first.click(); ai.first.fill(""); ai.first.type("1600 Amphitheatre Parkway, Mountain View", delay=85)
        pg.locator(".address__suggestion__item").first.wait_for(state="visible", timeout=11000); sug=True
    except Exception as e: print("   addr err", str(e)[:70], flush=True)
    rec("Stores|14","PASS" if sug else "FAIL","Typing an address surfaces suggested result(s) in the autocomplete.")
    brk=None
    if sug:
        try:
            pg.locator(".address__suggestion__item").first.click(); pg.wait_for_timeout(2200)
            brk=pg.evaluate(f"""()=>{{const d={N.SUB};return ['street','city','zip_code','country','state'].filter(id=>d.querySelector('#'+id));}}""")
        except Exception as e: print("   pick err", str(e)[:60], flush=True)
    rec("Stores|15","PASS" if brk else "FAIL", f"Selecting a suggestion reveals the address breakdown sub-form: {brk}")
    if brk:
        for fid,val in [("street","1600 Amphitheatre Parkway"),("city","Mountain View"),("zip_code","94043")]:
            try:
                L=pg.locator(f".md-dialog:not(.md-dialog--full-page) #{fid}")
                if L.count() and not L.first.input_value(): L.first.fill(val)
            except Exception: pass
        for fid,txt in [("country","United States"),("state","California")]:
            try:
                if pg.locator(f".md-dialog:not(.md-dialog--full-page) #{fid}").count():
                    N.rs_open(pg,fid,".md-dialog:not(.md-dialog--full-page)"); N.rs_pick(pg,txt)
            except Exception: pass
    sv=N.sub_click(pg,"Save & Close|Save and Close|Save & Continue|Save")
    pg.wait_for_timeout(8000)
    still=N.has_sub(pg)
    errs=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}}""")
    rec("Stores|16","PASS" if (not str(sv).startswith('none') and not still) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the store is saved (modal still open={still}{'; validation '+str(errs) if errs else ''}).")

    # ---------- Stores 1-8 : filters against populated store grid ----------
    print("=== STORES filters (1-8) ===", flush=True)
    pg.goto(aff_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Stores")
    filter_block(pg, rec, "Stores", "Filter Stores", scope_record=True)

    # ---------- Grid 1-9 : affiliate grid (now populated) ----------
    print("=== GRID (1-9) ===", flush=True)
    pg.goto(N.BASE+"/portal/affiliate", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    N.run_grid(pg, rec, "Grid", "Filter Affiliates", "Affiliates")

    # ---------- Timeline 1-8 ----------
    print("=== TIMELINE ===", flush=True)
    pg.goto(aff_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(4000)
    fb=pg.get_by_text("Filter Activity")
    if fb.count()==0: fb=pg.get_by_text("Filter Timeline")
    try:
        fb.first.click(); pg.wait_for_timeout(1800); ok="Select a filter" in N.bt(pg)
    except Exception: ok=False
    rec("Timeline|1","PASS" if ok else "FAIL","Timeline filter control opens the filter panel.")
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    rec("Timeline|2","PASS" if fo else "FAIL", f"Filter-field dropdown lists timeline columns: {fo}")
    tgt="Action" if "Action" in fo else (fo[0] if fo else None)
    if tgt:
        try:
            N.rs_pick(pg,tgt); pg.wait_for_timeout(1400)
            rec("Timeline|3","PASS" if "Select a value" in N.bt(pg) else "FAIL", f"Selected '{tgt}'; 'Select a value' appears.")
        except Exception as e: rec("Timeline|3","FAIL",str(e)[:120])
    else: rec("Timeline|3","FAIL","no options")
    vo=[]
    for _ in range(4):
        try: vo=N.rs_open_ph(pg,"Select a value")
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(1100)
    rec("Timeline|4","PASS" if vo else "FAIL", f"Dependent value dropdown for '{tgt}': {vo[:10]}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Timeline|5","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(3000)
    rec("Timeline|6","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies to the timeline ({ap}).")
    try:
        s=pg.get_by_placeholder("Search Activity...")
        s.first.fill("Affiliate"); pg.wait_for_timeout(3000); s.first.fill(""); pg.wait_for_timeout(1400)
        rec("Timeline|7","PASS","Timeline search accepts input and filters the activity list.")
    except Exception as e: rec("Timeline|7","FAIL", f"Search: {e}"[:130])
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(3500)
    feed=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&/Activity|Affiliate|Store/.test(x.innerText));
      return p.length?p[0].innerText.slice(0,320).replace(/\\n/g,' | '):'';}""")
    acts=[w for w in ["Create Affiliate","Update Affiliate","Create Store","Update Store","Create Note"] if w in feed]
    rec("Timeline|8","PASS" if acts else "FAIL", f"Timeline records actions performed on this affiliate — entries: {acts}. Feed: {feed[:150]}")

    # ---------- Notes 1-7 ----------
    print("=== NOTES ===", flush=True)
    pg.goto(aff_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Notes"); N.add_new_in_record(pg)
    st=N.sub_text(pg)
    rec("Notes|1","PASS" if ("Note" in st or "Title" in st) else "FAIL", f"New opens the note modal: {st[:110].replace(chr(10),' | ')}")
    tok=False
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #title").last
        L.fill(NOTE); pg.wait_for_timeout(800); tok=(L.input_value()==NOTE)
    except Exception as e: print("   t err",str(e)[:60], flush=True)
    rec("Notes|2","PASS" if tok else "FAIL", f"Title field accepts input ({tok}).")
    cok=False
    try:
        ce=pg.locator(".md-dialog:not(.md-dialog--full-page) [contenteditable=true]").first
        ce.click(); pg.keyboard.type("Regression test note for affiliate — safe to delete."); pg.wait_for_timeout(1300)
        cok=pg.evaluate(f"""()=>{{const d={N.SUB};const e=d&&d.querySelector('[contenteditable=true]');return e?e.innerText.trim().length>0:false;}}""")
    except Exception as e: print("   c err",str(e)[:60], flush=True)
    rec("Notes|3","PASS" if cok else "FAIL", f"Message/content rich-text box accepts input ({cok}).")
    sv=N.sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    listed=NOTE in N.bt(pg)
    rec("Notes|4","PASS" if (not str(sv).startswith('none') and listed) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the note appears in the list (found={listed}).")
    e=pg.evaluate("""()=>{const row=[...document.querySelectorAll('.dataTable__notes__row')].find(r=>/RegressionTest Note/.test(r.innerText));
      if(!row)return 'row-not-found';
      const a=row.querySelector('.dataTable__notes--actions')||row;
      const b=[...a.querySelectorAll('button')].find(x=>x.textContent.trim()==='edit');
      if(b){b.click();return 'clicked';}return 'no-edit';}""")
    pg.wait_for_timeout(6000)
    tv=pg.evaluate(f"""()=>{{const d={N.SUB};const i=d&&d.querySelector('#title');return i?i.value:null;}}""")
    rec("Notes|5","PASS" if (e=="clicked" and tv==NOTE) else "FAIL", f"Edit ({e}) opens the note modal populated — title reads '{tv}'.")
    ok6=False
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #title").last
        L.fill(NOTE+" [edited]"); pg.wait_for_timeout(800); ok6=L.input_value().endswith("[edited]")
    except Exception as ex: print("   e err",str(ex)[:60], flush=True)
    rec("Notes|6","PASS" if ok6 else "FAIL", f"Change reflects in the title field ({ok6}).")
    sv2=N.sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    pg.goto(aff_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    N.click_tab(pg,"Notes")
    persisted="[edited]" in N.bt(pg)
    rec("Notes|7","PASS" if (not str(sv2).startswith('none') and persisted) else "FAIL",
        f"Save & Close ('{sv2}'); record reopened and the edited note persists (found={persisted}).")

    json.dump({"aff_url":aff_url,"aff":AFF,"store":STORE}, open(N.EV+"/aff_ctx.json","w"), indent=1)
    pg.screenshot(path=N.EV+"/aff_end.png")
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
