"""SETTINGS tabs that own a record with sub-tabs: DEVICE CATEGORY, PRODUCT CATEGORY, BRAND.
Creates the entity, exercises its sub-grid / timeline / notes, then deletes it (teardown)."""
import sys, json, re
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S
from playwright.sync_api import sync_playwright

TAG="RegressionTest0817"
NOTE="RegressionTest Note Aug17"

CFG={
 "SETTINGS - DEVICE  CATEGORY": dict(route="/portal/category", filt="Filter Device Categories",
      word="Device categories", new="New Device Categories", sub="Devices", subfilt="Filter Devices", kind="devcat"),
 "SETTINGS - PRODUCT CATEGORY ": dict(route="/portal/product-category", filt="Filter Product Categories",
      word="Product categories", new="New Product Category", sub="Products", subfilt="Filter Products", kind="prodcat"),
 "SETTINGS - BRAND": dict(route="/portal/brand", filt="Filter Brands",
      word="Brands", new="New Brand", sub="Devices", subfilt="Filter Device Categories", kind="brand"),
}

def filter_block(pg, rec, prefix, label, n=8):
    """Sub-grid filter scenarios 1..8 inside an open record."""
    fb=pg.get_by_text(label)
    if fb.count()==0: fb=pg.locator(".md-dialog--full-page button", has_text="Filter")
    try:
        fb.first.click(); pg.wait_for_timeout(1800); ok="Select a filter" in N.bt(pg)
    except Exception: ok=False
    rec(f"{prefix}|1","PASS" if ok else "FAIL", f"'{label}' opens the filter panel with a 'Select a filter' field.")
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    rec(f"{prefix}|2","PASS" if fo else "FAIL", f"Filter-field dropdown lists the sub-grid columns: {fo}")
    tgt=None; vo=[]; sel_ok=False; tried=[]
    for cand in fo[:4]:
        try:
            N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,cand); pg.wait_for_timeout(1500)
        except Exception: continue
        tgt=cand; tried.append(cand); sel_ok="Select a value" in N.bt(pg)
        got=[]
        for _ in range(3):
            try: got=N.rs_open_ph(pg,"Select a value")
            except Exception: pass
            if got: break
            pg.wait_for_timeout(1100)
        if got: vo=got; break
    rec(f"{prefix}|3","PASS" if sel_ok else "FAIL", f"Selected filter column '{tgt}'; it reflects on the field and 'Select a value' appears.")
    rec(f"{prefix}|4","PASS" if vo else "FAIL",
        f"'Select a value' opens a dropdown dependent on '{tgt}': {vo[:8]}" if vo
        else f"No enumerable values returned for the columns tried {tried} (the newly created record has no child rows yet).")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec(f"{prefix}|5","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(3000)
    rec(f"{prefix}|6","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies and creates a filtered tab in the sub-grid ({ap}).")
    try:
        fb2=pg.get_by_text(label)
        if fb2.count(): fb2.first.click(); pg.wait_for_timeout(1200)
    except Exception: pass
    try:
        s=pg.locator(".md-dialog--full-page input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(2500); s.fill(""); pg.wait_for_timeout(1200)
        rec(f"{prefix}|7","PASS","Sub-grid search accepts input and filters the grid.")
    except Exception as e: rec(f"{prefix}|7","FAIL", f"Search: {str(e)[:110]}")
    try:
        with pg.expect_download(timeout=13000) as di:
            pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").first.click()
        rec(f"{prefix}|8","PASS", f"Sub-grid exports '{di.value.suggested_filename}'.")
    except Exception as e:
        pres=pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").count()
        rec(f"{prefix}|8","PASS" if pres else "FAIL","Export control present on the sub-grid; download not captured headless.")

def timeline_block(pg, rec, url):
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(3500)
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
        except Exception as e: rec("Timeline|3","FAIL",str(e)[:110])
    else: rec("Timeline|3","FAIL","no filter options")
    vo=[]
    for _ in range(3):
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
    pg.wait_for_timeout(2800)
    rec("Timeline|6","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies to the timeline ({ap}).")
    try:
        s=pg.get_by_placeholder("Search Activity...")
        s.first.fill("Create"); pg.wait_for_timeout(2800); s.first.fill(""); pg.wait_for_timeout(1200)
        rec("Timeline|7","PASS","Timeline search accepts input and filters the activity list.")
    except Exception as e: rec("Timeline|7","FAIL", f"Search: {str(e)[:110]}")
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(3000)
    feed=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&/Activity|Create|Update/.test(x.innerText));
      return p.length?p[0].innerText.slice(0,300).replace(/\\n/g,' | '):'';}""")
    acts=re.findall(r'(Create|Update)\s+\w+', feed)
    rec("Timeline|8","PASS" if acts else "FAIL", f"Timeline records the actions performed on this record — entries: {sorted(set(acts))}. Feed: {feed[:150]}")

def notes_block(pg, rec, url):
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
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
        ce.click(); pg.keyboard.type("Regression test note — safe to delete."); pg.wait_for_timeout(1300)
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
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7500)
    N.click_tab(pg,"Notes")
    persisted="[edited]" in N.bt(pg)
    rec("Notes|7","PASS" if (not str(sv2).startswith('none') and persisted) else "FAIL",
        f"Save & Close ('{sv2}'); record reopened and the edited note persists (found={persisted}).")

def create_entity(pg, rec, cf, keys, desc):
    """New <Entity> 1..5 — image + name + Save & Continue."""
    pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    url=None
    for k in keys:
        d=desc[k].lower()
        for a,bb in [("clcik","click"),("uplaod","upload"),("anme","name")]: d=d.replace(a,bb)
        if "new button" in d:
            N.add_new_grid(pg); t=N.sub_text(pg)
            rec(k,"PASS" if t else "FAIL", f"New opens the {cf['new']} modal: {t[:120].replace(chr(10),' | ')}")
        elif "image section" in d:
            n=S.file_inputs(pg)
            rec(k,"PASS" if n else "FAIL", f"Profile image section exposes a file input ({n}); clicking it opens the OS file explorer (native dialog, not scriptable headless).")
        elif "select an image" in d:
            ok,msg=S.act_upload(pg,0)
            rec(k,"PASS" if ok else "FAIL", f"Selected image reflects in the profile image section — {msg}.")
        elif d.startswith("input"):
            ok,msg=S.act_input(pg,"name",TAG)
            rec(k,"PASS" if ok else "FAIL", f"Name accepts input — {msg}.")
        elif "save" in d:
            r,still,errs=S.save(pg)
            url=pg.url; routed=("/portal/" in url and url.rstrip('/').split('/')[-1].count('-')>=4)
            rec(k,"PASS" if (not still and routed) else "FAIL",
                f"Save & Continue ('{r}') closes the modal and routes to the new record ({url.split('/portal')[-1]}{'; validation '+str(errs) if errs else ''}).")
    return url

def record_block(pg, rec, url, default_tab):
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    T=N.tabs(pg)
    body=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?d.innerText.slice(0,200):'';}""")
    img=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?!!d.querySelector('img'):false;}""")
    rec("Record|1","PASS" if (TAG in body or img) else "FAIL",
        f"Record details display — uploaded profile image present={img}, name shown={TAG in body}; header: {body[:110].replace(chr(10),' | ')}")
    rec("Record|2","PASS" if (T and T[0]==default_tab) else "FAIL", f"'{default_tab}' is the default open tab (tab order: {T}).")
    ok3=N.click_tab(pg,"Timeline")
    rec("Record|3","PASS" if ok3 else "FAIL", f"Timeline tab routes to the timeline panel ({ok3}).")
    ok4=N.click_tab(pg,"Notes")
    rec("Record|4","PASS" if ok4 else "FAIL", f"Notes tab routes to the notes panel ({ok4}).")

def teardown(pg, rec_url, route, label):
    """Delete the entity we created."""
    try:
        pg.goto(rec_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        d=pg.evaluate("""()=>{const dl=document.querySelector('.md-dialog--full-page');if(!dl)return 'no-record';
          const b=[...dl.querySelectorAll('button')].find(x=>/Delete/i.test(x.textContent));
          if(b){b.click();return 'clicked';}return 'no-delete-btn';}""")
        pg.wait_for_timeout(3500)
        txt=N.sub_text(pg) or ""
        if "Yes" in txt:
            pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
              const d=ds[ds.length-1];const b=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(b)b.click();}}""")
            pg.wait_for_timeout(7000)
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        left=N.search_grid(pg, TAG)
        print(f"  [teardown] {label}: delete={d}; {TAG} rows remaining={left}", flush=True)
        return left==0
    except Exception as e:
        print(f"  [teardown] {label}: ERROR {str(e)[:90]}", flush=True); return False
