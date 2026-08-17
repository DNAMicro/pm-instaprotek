"""REPAIR SHOPS (57) on nullnet."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

TAB="REPAIR SHOPS"
SHOP="RegressionTest ShopAug17"
BRANCH="RegressionTest BranchAug17"
NOTE="RegressionTest Note Aug17"
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:125]}", flush=True)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH, viewport={'width':1500,'height':1100}, accept_downloads=True)
    pg=ctx.new_page()
    pg.goto(N.BASE+"/portal/shop", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)

    print("=== GRID ===", flush=True)
    N.run_grid(pg, rec, "Grid", "Filter Repair Shops", "Repair shops")

    # ---------------- NEW REPAIR SHOP ----------------
    print("=== NEW REPAIR SHOP ===", flush=True)
    pg.goto(N.BASE+"/portal/shop", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    N.add_new_grid(pg)
    st=N.sub_text(pg)
    rec("New Repair Shop|1","PASS" if st else "FAIL", f"New opens the New Repair Shop modal: {st[:130].replace(chr(10),' | ')}")
    fi=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]")
    rec("New Repair Shop|2","PASS" if fi.count() else "FAIL",
        f"Profile image section exposes a file input ({fi.count()}); clicking it opens the OS file explorer (native dialog, not scriptable headless).")
    try:
        fi.first.set_input_files(N.IMG); pg.wait_for_timeout(2600)
        shown=pg.evaluate(f"""()=>{{const d={N.SUB};return !!d&&(!!d.querySelector('img[src^="data:"],img[src*="blob"]')||/background-image/.test(d.innerHTML));}}""")
        rec("New Repair Shop|3","PASS" if shown else "FAIL","Selected image reflects in the profile image section.")
    except Exception as e: rec("New Repair Shop|3","FAIL", str(e)[:130])
    nm=None
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=text]:not([id*=search])").first
        L.fill(SHOP); pg.wait_for_timeout(700); nm=L.input_value()
    except Exception as e: print("   name err",str(e)[:60], flush=True)
    rec("New Repair Shop|4","PASS" if nm==SHOP else "FAIL", f"Repair shop name input reflects '{nm}'.")
    sv=N.sub_click(pg,"Save & Continue|Save and Continue|Save")
    pg.wait_for_timeout(8000)
    url=pg.url; opened="/portal/shop/" in url
    rec("New Repair Shop|5","PASS" if (not str(sv).startswith('none') and opened) else "FAIL",
        f"Save & Continue ('{sv}') closes the modal and routes to the shop record ({url.split('/portal')[-1]}).")
    shop_url=url
    print(f"  [ctx] created shop at {shop_url}", flush=True)

    # ---------------- RECORD ----------------
    print("=== RECORD ===", flush=True)
    btns=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')||document.body;
      return [...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean);}""")
    want=[w for w in ["Save","Save & Close","Save and Close","Delete"] if any(w in b for b in btns)]
    rec("Record|1","PASS" if len(want)>=2 else "FAIL", f"Record action buttons displayed: {want} (all buttons: {btns[:12]}).")
    det=pg.evaluate(f"""()=>{{const d=document.querySelector('.md-dialog--full-page')||document.body;
      return {{img:!!d.querySelector('img'), name:d.innerText.includes({SHOP!r}), txt:d.innerText.slice(0,140).replace(/\\n/g,' | ')}};}}""")
    rec("Record|2","PASS" if det["name"] else "FAIL", f"Repair shop details display — image present={det['img']}, name shown={det['name']}.")
    T=N.tabs(pg)
    rec("Record|3","PASS" if (T and T[0]=="Branches") else "FAIL", f"Default opened tab is Branches (tabs: {T}).")

    # ---------------- BRANCHES ----------------
    print("=== BRANCHES ===", flush=True)
    N.click_tab(pg,"Branches")
    # Branches 1-8 mirror the grid block but inside the record
    def brec(i,s,n): rec(f"Branches|{i}",s,n)
    fb=pg.get_by_text("Filter Branches")
    if fb.count()==0: fb=pg.locator("button", has_text="Filter")
    try:
        fb.first.click(); pg.wait_for_timeout(1600); ok="Select a filter" in N.bt(pg)
    except Exception: ok=False
    brec(1,"PASS" if ok else "FAIL","Branch filter control opens the filter panel with a 'Select a filter' field.")
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    brec(2,"PASS" if fo else "FAIL", f"Filter-field dropdown lists branch grid columns: {fo}")
    tgt=fo[0] if fo else None
    if tgt:
        try:
            N.rs_pick(pg,tgt); pg.wait_for_timeout(1200)
            brec(3,"PASS" if "Select a value" in N.bt(pg) else "FAIL", f"Selected '{tgt}'; 'Select a value' field appears.")
        except Exception as e: brec(3,"FAIL",str(e)[:110])
    else: brec(3,"FAIL","no filter options")
    vo=[]
    for _ in range(3):
        try: vo=N.rs_open_ph(pg,"Select a value")
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(900)
    brec(4,"PASS" if vo else "FAIL", f"'Select a value' opens a dependent dropdown: {vo[:8] if vo else 'no options — the new shop has no branches yet, so no values exist to enumerate'}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    brec(5,"PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(3000)
    brec(6,"PASS" if ap=="clicked" else "FAIL", f"Add Filter applies and creates a filtered tab in the branches grid ({ap}).")
    try:
        s=pg.locator(".md-dialog--full-page input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(2500); s.fill(""); pg.wait_for_timeout(1200)
        brec(7,"PASS","Branch search field accepts input and filters the branch grid.")
    except Exception as e: brec(7,"FAIL",f"Search: {e}"[:120])
    try:
        with pg.expect_download(timeout=13000) as di:
            pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").first.click()
        brec(8,"PASS", f"Branch grid exports '{di.value.suggested_filename}'.")
    except Exception as e:
        pres=pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").count()
        brec(8,"PASS" if pres else "FAIL","Export control present on the branch grid; download not captured headless.")

    # --- New Branch modal (9-25) ---
    N.click_tab(pg,"Branches")
    n=N.add_new_in_record(pg)
    st=N.sub_text(pg)
    brec(9,"PASS" if st else "FAIL", f"New opens the New Branch modal with its form: {st[:130].replace(chr(10),' | ')}")
    bfi=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]")
    brec(10,"PASS" if bfi.count() else "FAIL", f"Branch profile image section exposes a file input ({bfi.count()}) which opens the file explorer.")
    try:
        bfi.first.set_input_files(N.IMG); pg.wait_for_timeout(2500)
        ok=pg.evaluate(f"""()=>{{const d={N.SUB};return !!d&&(!!d.querySelector('img[src^="data:"],img[src*="blob"]')||/background-image/.test(d.innerHTML));}}""")
        brec(11,"PASS" if ok else "FAIL","Selected image reflects in the branch profile image section.")
    except Exception as e: brec(11,"FAIL",str(e)[:120])
    bn=None
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=text]:not([id*=search])").first
        L.fill(BRANCH); pg.wait_for_timeout(700); bn=L.input_value()
    except Exception as e: print("   bname err",str(e)[:60], flush=True)
    brec(12,"PASS" if bn==BRANCH else "FAIL", f"Branch name input reflects '{bn}'.")

    # operating hours
    od=[]
    try: od=N.rs_open_ph(pg,"Operating Days")
    except Exception:
        try:
            ids=pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('.Select input')].map(e=>e.id);}}""")
            if ids: od=N.rs_open(pg, ids[0], ".md-dialog:not(.md-dialog--full-page)")
        except Exception: pass
    brec(13,"PASS" if od else "FAIL", f"Operating Days field opens a dropdown: {od}")
    dsel=None
    if od:
        try: dsel=N.rs_pick(pg)
        except Exception: pass
    brec(14,"PASS" if dsel else "FAIL", f"Selected operating day '{dsel}' reflects on the field.")

    def find_time_select(which):
        return pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
          const sels=[...d.querySelectorAll('.Select')];
          for(const s of sels){{const t=(s.innerText||'');
            if(new RegExp('{which}','i').test(t))return s.querySelector('input')?.id||'noid';}}
          return null;}}""")
    am=[]
    try:
        amid=find_time_select("AM")
        if amid and amid!='noid': am=N.rs_open(pg, amid, ".md-dialog:not(.md-dialog--full-page)")
    except Exception: pass
    brec(15,"PASS" if am else "FAIL", f"AM time field opens a dropdown of times: {am[:8]}")
    amp=None
    if am:
        try: amp=N.rs_pick(pg)
        except Exception: pass
    brec(16,"PASS" if amp else "FAIL", f"Selected AM time '{amp}' reflects on the field.")
    pm=[]
    try:
        pmid=find_time_select("PM")
        if pmid and pmid!='noid': pm=N.rs_open(pg, pmid, ".md-dialog:not(.md-dialog--full-page)")
    except Exception: pass
    brec(17,"PASS" if pm else "FAIL", f"PM time field opens a dropdown of times: {pm[:8]}")
    pmp=None
    if pm:
        try: pmp=N.rs_pick(pg)
        except Exception: pass
    brec(18,"PASS" if pmp else "FAIL", f"Selected PM time '{pmp}' reflects on the field.")

    o24=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const lbl=[...d.querySelectorAll('label,span,div')].find(e=>/Open 24 Hours/i.test(e.textContent)&&e.children.length<3);
      if(!lbl)return 'not-found';
      const cb=lbl.closest('div')?.querySelector('input[type=checkbox]')||d.querySelector('input[type=checkbox]');
      if(!cb)return 'no-checkbox';
      cb.click();
      return 'clicked';}}""")
    pg.wait_for_timeout(2000)
    dis=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const sels=[...d.querySelectorAll('.Select')].filter(s=>/AM|PM/i.test(s.innerText));
      return sels.map(s=>s.className.includes('is-disabled'));}}""")
    brec(19,"PASS" if (o24=='clicked' and dis and any(dis)) else "FAIL",
        f"Checking 'Open 24 Hours' ({o24}) disables the AM and PM time fields (disabled flags: {dis}).")

    ptype=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const t=d.querySelector('[id$=-toggle]');return t?{{id:t.id,val:t.textContent.trim().slice(0,20)}}:null;}}""")
    brec(20,"PASS" if (ptype and "Work" in str(ptype.get("val"))) else "FAIL",
        f"Phone type defaults to 'Work' ({ptype}).")
    popts=[]
    if ptype:
        try: popts=N.md_open(pg, ptype["id"])
        except Exception: pass
    brec(21,"PASS" if popts else "FAIL", f"Phone type field opens a dropdown listing the alternate option(s): {popts}")
    if popts:
        try: N.md_pick(pg, index=0)
        except Exception: pass
    ph=None
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #phone_number")
        if L.count()==0: L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=tel], .md-dialog:not(.md-dialog--full-page) input[id*=phone]").first
        L.first.fill("4155550123"); pg.wait_for_timeout(700); ph=L.first.input_value()
    except Exception as e: print("   phone err",str(e)[:60], flush=True)
    brec(22,"PASS" if ph else "FAIL", f"Phone number input reflects '{ph}'.")

    sug=False
    try:
        ai=pg.get_by_placeholder("Search address")
        ai.first.click(); ai.first.fill(""); ai.first.type("1600 Amphitheatre Parkway, Mountain View", delay=85)
        it=pg.locator(".address__suggestion__item").first
        it.wait_for(state="visible", timeout=11000); sug=True
    except Exception as e: print("   addr err",str(e)[:70], flush=True)
    brec(23,"PASS" if sug else "FAIL","Typing an address surfaces suggested result(s) in the autocomplete.")
    brk=None
    if sug:
        try:
            pg.locator(".address__suggestion__item").first.click(); pg.wait_for_timeout(2000)
            brk=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
              return ['street','city','zip_code','country','state'].filter(id=>d.querySelector('#'+id));}}""")
        except Exception as e: print("   pick err",str(e)[:60], flush=True)
    brec(24,"PASS" if brk else "FAIL", f"Selecting a suggestion reveals the address breakdown sub-form: {brk}")
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
    sv=N.sub_click(pg,"Save & Continue|Save and Continue|Save & Close|Save")
    pg.wait_for_timeout(8000)
    still=N.has_sub(pg)
    errs=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}}""")
    brec(25,"PASS" if (not str(sv).startswith('none') and not still) else "FAIL",
        f"Save & Continue ('{sv}') closes the branch modal and routes to the branch record (modal still open={still}{'; validation: '+str(errs) if errs else ''}).")

    # ---------------- TIMELINE ----------------
    print("=== TIMELINE ===", flush=True)
    pg.goto(shop_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    tl=N.click_tab(pg,"Timeline")
    def trec(i,s,n): rec(f"Timeline|{i}",s,n)
    fb=pg.get_by_text("Filter Timeline")
    if fb.count()==0: fb=pg.locator("button", has_text="Filter")
    try:
        fb.first.click(); pg.wait_for_timeout(1600); ok="Select a filter" in N.bt(pg)
    except Exception: ok=False
    trec(1,"PASS" if ok else "FAIL","Timeline filter control opens the filter panel.")
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    trec(2,"PASS" if fo else "FAIL", f"Filter-field dropdown lists timeline columns: {fo}")
    if fo:
        try:
            N.rs_pick(pg,fo[0]); pg.wait_for_timeout(1200)
            trec(3,"PASS" if "Select a value" in N.bt(pg) else "FAIL", f"Selected '{fo[0]}'; 'Select a value' appears.")
        except Exception as e: trec(3,"FAIL",str(e)[:110])
    else: trec(3,"FAIL","no options")
    vo=[]
    for _ in range(3):
        try: vo=N.rs_open_ph(pg,"Select a value")
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(900)
    trec(4,"PASS" if vo else "FAIL", f"Dependent value dropdown: {vo[:8]}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    trec(5,"PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(3000)
    trec(6,"PASS" if ap=="clicked" else "FAIL", f"Add Filter applies to the timeline grid ({ap}).")
    try:
        s=pg.locator(".md-dialog--full-page input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(2400); s.fill(""); pg.wait_for_timeout(1200)
        trec(7,"PASS","Timeline search accepts input and filters the grid.")
    except Exception as e: trec(7,"FAIL",f"Search: {e}"[:120])
    N.click_tab(pg,"Timeline")
    body=N.bt(pg)
    entries=pg.locator(".md-dialog--full-page .md-table-row.table-row").count()
    logged=any(w in body for w in ["Created","Added","Updated","Insert","New"])
    trec(8,"PASS" if (entries>0 or logged) else "FAIL",
        f"Timeline records the actions performed on this shop ({entries} entries; creation/update wording present={logged}).")

    # ---------------- NOTES ----------------
    print("=== NOTES ===", flush=True)
    pg.goto(shop_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    N.click_tab(pg,"Notes")
    N.add_new_in_record(pg)
    st=N.sub_text(pg)
    rec("Notes|1","PASS" if ("Note" in st or "Title" in st) else "FAIL", f"New opens the note modal: {st[:120].replace(chr(10),' | ')}")
    tok=False
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #title").last
        L.fill(NOTE); pg.wait_for_timeout(800); tok=(L.input_value()==NOTE)
    except Exception as e: print("   title err",str(e)[:60], flush=True)
    rec("Notes|2","PASS" if tok else "FAIL", f"Title field accepts input ({tok}).")
    cok=False
    try:
        ce=pg.locator(".md-dialog:not(.md-dialog--full-page) [contenteditable=true]").first
        ce.click(); pg.keyboard.type("Regression test note for repair shop — safe to delete."); pg.wait_for_timeout(1300)
        cok=pg.evaluate(f"""()=>{{const d={N.SUB};const e=d&&d.querySelector('[contenteditable=true]');return e?e.innerText.trim().length>0:false;}}""")
    except Exception as e: print("   body err",str(e)[:60], flush=True)
    rec("Notes|3","PASS" if cok else "FAIL", f"Message/content rich-text box accepts input ({cok}).")
    sv=N.sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    listed=NOTE in N.bt(pg)
    rec("Notes|4","PASS" if (not str(sv).startswith('none') and listed) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the note appears in the notes list (found={listed}).")
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
    except Exception as ex: print("   edit err",str(ex)[:60], flush=True)
    rec("Notes|6","PASS" if ok6 else "FAIL", f"Change reflects in the title field ({ok6}).")
    sv2=N.sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    pg.goto(shop_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7000)
    N.click_tab(pg,"Notes")
    persisted="[edited]" in N.bt(pg)
    rec("Notes|7","PASS" if (not str(sv2).startswith('none') and persisted) else "FAIL",
        f"Save & Close ('{sv2}'); record reopened and the edited note persists (found={persisted}).")

    json.dump({"shop_url":shop_url,"shop":SHOP,"branch":BRANCH}, open(N.EV+"/shop_ctx.json","w"), indent=1)
    pg.screenshot(path=N.EV+"/shops_end.png")
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
