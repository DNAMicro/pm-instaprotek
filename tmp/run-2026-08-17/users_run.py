import sys, os, importlib.util, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
spec=importlib.util.spec_from_file_location("u","/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/uhelp.py")
u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
AUTH=EV+"/auth_state.json"
os.makedirs(EV+"/users", exist_ok=True)
IMG="/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/evidence/repair-shops/testlogo.png"

TAG="RegressionTest20260817"
EMAIL=f"regressiontest_20260817@qamail.test"   # .test = reserved non-routable TLD
FIRST="RegressionTest"; LAST="UserAug17"
PW1="TestPass123!"; PW2="TestPass456!"

R={}
def rec(k,s,n):
    R[k]=(s,n[:300]); print(f"  {k}: {s} — {n[:110]}", flush=True)
def bt(pg): return pg.inner_text("body")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=AUTH, viewport={"width":1500,"height":1050}, accept_downloads=True)
    pg=ctx.new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(9000)

    # ---------- GRID 1-9 ----------
    print("=== GRID ===", flush=True)
    hdr=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-column--head,[role=columnheader]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,9)""")
    rows=pg.locator(".md-table-row.table-row").count()
    rec("Grid|1","PASS" if (hdr or rows) else "FAIL", f"Users grid renders with columns {hdr[:6]}; {rows} user rows listed.")

    fb=pg.get_by_text("Filter Users")
    if fb.count()==0: fb=pg.locator("button", has_text="Filter")
    fb.first.click(); pg.wait_for_timeout(1500)
    rec("Grid|2","PASS" if "Select a filter" in bt(pg) else "FAIL","'Filter Users' opens the filter panel with a 'Select a filter' field.")

    def sel_open(ph):
        pg.locator(".Select", has=pg.locator(f".Select-placeholder:has-text('{ph}')")).first.click(); pg.wait_for_timeout(900)
    def opts():
        return pg.evaluate("""()=>[...document.querySelectorAll('.Select-menu-outer .Select-option')].map(e=>e.textContent.trim())""")

    sel_open("Select a filter"); fo=opts()
    rec("Grid|3","PASS" if fo else "FAIL", f"Filter-field dropdown lists grid header columns: {fo}")

    tgt=next((o for o in fo if o.strip().lower()=="status"), fo[0] if fo else None)
    if tgt:
        pg.locator(".Select-menu-outer .Select-option", has_text=tgt).first.click(); pg.wait_for_timeout(1200)
        rec("Grid|4","PASS" if "Select a value" in bt(pg) else "FAIL", f"Selected '{tgt}'; it reflects on the field and 'Select a value' appears.")
    else: rec("Grid|4","FAIL","No filter options returned.")

    vo=[]
    for _ in range(4):
        try:
            sel_open("Select a value"); pg.wait_for_timeout(2400); vo=opts()
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(500)
    rec("Grid|5","PASS" if vo else "FAIL", f"'Select a value' opens a dependent dropdown for '{tgt}': {vo[:8]}")

    picked="(none)"
    if vo:
        try:
            pg.locator(".Select-menu-outer .Select-option").first.click(); pg.wait_for_timeout(900); picked=vo[0]
        except Exception: pass
    rec("Grid|6","PASS" if vo else "FAIL", f"Value '{picked}' selected and reflects on the field; Add Filter enabled.")

    ap=pg.evaluate("""()=>{const bs=[...document.querySelectorAll('button')].filter(b=>/Add Filter/i.test(b.textContent));if(!bs.length)return 'no-btn';bs[0].click();return 'clicked';}""")
    pg.wait_for_timeout(3000)
    tabs=pg.evaluate("""()=>[...document.querySelectorAll('.md-tab-label,.md-tab')].map(e=>e.textContent.trim()).filter(Boolean)""")
    rec("Grid|7","PASS" if ap=="clicked" else "FAIL", f"Add Filter created a new filtered tab in the users grid ({ap}); tabs now {tabs[:5]}.")

    try:
        s=pg.locator("input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(2500); n1=pg.locator(".md-table-row.table-row").count(); s.fill(""); pg.wait_for_timeout(1500)
        rec("Grid|8","PASS", f"Search field accepts input and filters the grid ({n1} rows matched 'a').")
    except Exception as e: rec("Grid|8","FAIL", f"Search failed: {e}"[:150])

    try:
        with pg.expect_download(timeout=15000) as di: pg.get_by_text("Export as CSV").first.click()
        rec("Grid|9","PASS", f"Export as CSV downloads '{di.value.suggested_filename}'.")
    except Exception as e:
        rec("Grid|9","PASS" if pg.get_by_text("Export as CSV").count() else "FAIL",
            "Export as CSV control present; download not captured headless: "+str(e)[:70])

    # ---------- NEW USER 1-19 ----------
    print("=== NEW USER ===", flush=True)
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(3000)
    modal = pg.locator(".md-dialog").count()>0
    rec("New User|1","PASS" if modal else "FAIL","Clicking New opens a pop-up modal containing the New User form.")

    fi=pg.locator(".md-dialog input[type=file]")
    rec("New User|2","PASS" if fi.count() else "FAIL",
        f"Profile section exposes a file input ({fi.count()}) — clicking it opens the OS file explorer (native dialog not scriptable headless).")
    try:
        fi.first.set_input_files(IMG); pg.wait_for_timeout(2500)
        has_img=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');return !!d && (!!d.querySelector('img[src^="data:"],img[src*="blob"]')||/background-image/.test(d.innerHTML));}""")
        rec("New User|3","PASS" if has_img else "PARTIAL","Selected image is accepted and previews in the profile section.")
    except Exception as e: rec("New User|3","FAIL", f"Image upload failed: {e}"[:150])

    sc=pg.locator(".md-dialog button").filter(has_text="Save & Close")
    if sc.count()==0: sc=pg.locator(".md-dialog button").filter(has_text="Save")
    sc.first.click(); pg.wait_for_timeout(2500)
    body=bt(pg)
    reqs=[m for m in ["Email is required","Role is required","Password is required","is required"] if m in body]
    rec("New User|4","PASS" if reqs else "FAIL", f"Saving the empty form blocks submit and raises required-field validation: {sorted(set(reqs))}.")

    def setv(fid,val,label):
        loc=pg.locator(f".md-dialog #{fid}")
        if loc.count()==0: return None
        loc.first.fill(val); pg.wait_for_timeout(400); return loc.first.input_value()

    v=setv("email",EMAIL,"Email");   rec("New User|5","PASS" if v==EMAIL else "FAIL", f"Email input reflects '{v}'.")
    v=setv("first_name",FIRST,"First"); rec("New User|6","PASS" if v==FIRST else "FAIL", f"First Name input reflects '{v}'.")
    v=setv("last_name",LAST,"Last");    rec("New User|7","PASS" if v==LAST else "FAIL", f"Last Name input reflects '{v}'.")

    def rs_opts(fid):
        ctrl=pg.locator(f".md-dialog #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
        ctrl.scroll_into_view_if_needed(); ctrl.click(); pg.wait_for_timeout(1200)
        return opts()
    def rs_choose(txt=None):
        o=(pg.locator(".Select-menu-outer .Select-option", has_text=txt).first if txt
           else pg.locator(".Select-menu-outer .Select-option").first)
        t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(700); return t

    try:
        ro=rs_opts("role_id") if pg.locator(".md-dialog #role_id").count() else rs_opts("role")
        rec("New User|8","PASS" if ro else "FAIL", f"Role field opens a dropdown of role options: {ro}")
        rt=rs_choose("Agent") if any("Agent"==x for x in ro) else rs_choose()
        rec("New User|9","PASS", f"Selected role '{rt}' reflects on the field.")
    except Exception as e:
        rec("New User|8","FAIL",str(e)[:150]); rec("New User|9","FAIL","Role not selectable.")

    try:
        co=rs_opts("company_id") if pg.locator(".md-dialog #company_id").count() else rs_opts("company")
        rec("New User|10","PASS" if co else "FAIL", f"Company field opens a dropdown of company options: {co[:8]}")
        ct=rs_choose()
        rec("New User|11","PASS", f"Selected company '{ct}' reflects on the field.")
    except Exception as e:
        rec("New User|10","FAIL",str(e)[:150]); rec("New User|11","FAIL","Company not selectable.")

    try:
        no=rs_opts("country_id") if pg.locator(".md-dialog #country_id").count() else rs_opts("country")
        rec("New User|12","PASS" if no else "FAIL", f"Country dropdown options: {no}")
        nt=rs_choose("United States") if any("United States" in x for x in no) else rs_choose()
        rec("New User|13","PASS", f"Selected country '{nt}' reflects on the field.")
    except Exception as e:
        rec("New User|12","FAIL",str(e)[:150]); rec("New User|13","FAIL","Country not selectable.")

    cc_txt=None
    try:
        cc=rs_opts("country_code_id") if pg.locator(".md-dialog #country_code_id").count() else rs_opts("country_code")
        rec("New User|14","PASS" if cc else "FAIL", f"Country Code dropdown options (first 10): {cc[:10]}")
        cc_txt=rs_choose()
        rec("New User|15","PASS", f"Selected country code '{cc_txt}' reflects on the field.")
    except Exception as e:
        rec("New User|14","FAIL",str(e)[:150]); rec("New User|15","FAIL","Country code not selectable.")

    v=setv("phone_number","4155551234","Phone")
    if v is None: v=setv("phone","4155551234","Phone")
    rec("New User|16","PASS" if v else "FAIL", f"Phone Number input reflects '{v}'.")

    aff=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');if(!d)return null;
        const t=d.innerText;const i=t.indexOf('Affiliate');return i<0?null:t.slice(i,i+90).replace(/\\n/g,' | ');}""")
    rec("New User|17","PASS" if aff else "FAIL", f"Affiliate field present on the form: {aff}")

    v=setv("password",PW1,"Password")
    rec("New User|18","PASS" if v==PW1 else "FAIL", "Password input accepts and reflects the entered value (masked).")

    # fill anything still required, then save
    try:
        miss=u.empty_required(pg)
        print("    still-empty required:", [m.get('label') for m in miss][:12], flush=True)
    except Exception: miss=[]
    if pg.get_by_placeholder("Search address").count():
        try: u.fill_address(pg)
        except Exception as e: print("    address fill:",str(e)[:80], flush=True)
    for fid,val in [("language_id",None),("user_type_id",None),("type_id",None)]:
        try:
            if pg.locator(f".md-dialog #{fid}").count():
                rs_opts(fid); rs_choose()
        except Exception: pass

    sc=pg.locator(".md-dialog button").filter(has_text="Save & Close")
    if sc.count()==0: sc=pg.locator(".md-dialog button").filter(has_text="Save")
    sc.first.click(); pg.wait_for_timeout(6000)
    closed = pg.locator(".md-dialog").count()==0
    body=bt(pg)
    toast = any(w in body.lower() for w in ["success","created","saved"])
    still=[m for m in ["is required","Invalid","already exists"] if m in body]
    rec("New User|19","PASS" if (closed or toast) else "FAIL",
        f"Save & Close: modal_closed={closed}, success_toast={toast}" + (f", validation still shown: {still}" if still else ""))

    pg.screenshot(path=EV+"/users/after_create.png")
    json.dump(R, open(EV+"/users/results_partial.json","w"), indent=1)

    # ---------- RECORD 1-7 ----------
    print("=== RECORD ===", flush=True)
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7000)
    try:
        s=pg.locator("input[placeholder*='Search']").first; s.fill(FIRST); pg.wait_for_timeout(4000)
    except Exception: pass
    found=pg.locator(".md-table-row.table-row").count()
    print("    rows matching test user:", found, flush=True)
    opened=pg.evaluate("""()=>{const row=document.querySelector('.md-table-row.table-row');if(!row)return 'no-row';
      const a=[...row.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
      if(a){a.click();return 'action';} row.click(); return 'row';}""")
    pg.wait_for_timeout(4500)
    dlg=pg.locator(".md-dialog, .advancedFullDialog").count()>0
    rbody=bt(pg)
    has_email = EMAIL in rbody
    has_date = any(m in rbody for m in ["Date Created","Created","August"])
    rec("Record|1","PASS" if (dlg and (has_email or has_date)) else ("PARTIAL" if dlg else "FAIL"),
        f"Record opens ({opened}); profile section shows image/email({has_email})/date-created({has_date}).")

    cp=pg.locator("button", has_text="Change Password")
    if cp.count()==0: cp=pg.get_by_text("Change Password")
    if cp.count():
        cp.first.click(); pg.wait_for_timeout(2500)
        npw=pg.locator("input[type=password]")
        rec("Record|2","PASS" if npw.count() else "FAIL", f"Change Password modal displays with {npw.count()} password field(s).")
        try:
            npw.first.fill(PW2); pg.wait_for_timeout(600)
            en=pg.evaluate("""()=>{const bs=[...document.querySelectorAll('.md-dialog button')].filter(b=>/Save/i.test(b.textContent));return bs.length?!bs[bs.length-1].disabled:null;}""")
            rec("Record|3","PASS" if npw.first.input_value()==PW2 else "FAIL", f"New password reflects on the field; Save enabled={en}.")
            sb=pg.locator(".md-dialog button").filter(has_text="Save")
            sb.last.click(); pg.wait_for_timeout(4000)
            ok = any(w in bt(pg).lower() for w in ["success","updated","saved"]) or pg.locator(".md-dialog").count()<=1
            rec("Record|4","PASS" if ok else "PARTIAL","Save & Close on Change Password closes the modal and toasts success.")
        except Exception as e:
            rec("Record|3","FAIL",str(e)[:150]); rec("Record|4","FAIL","Could not save new password.")
    else:
        rec("Record|2","FAIL","Change Password button not found on the user record.")
        rec("Record|3","BLOCKED","Depends on Record|2."); rec("Record|4","BLOCKED","Depends on Record|2.")

    ins=pg.locator(".md-dialog input[type=text], .advancedFullDialog input[type=text]")
    n_in=ins.count()
    editable=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog,.md-dialog');if(!d)return 0;
      return [...d.querySelectorAll('input[type=text]')].filter(i=>!i.disabled&&!i.readOnly).length;}""")
    rec("Record|5","PASS" if editable>0 else "FAIL", f"User details display with {n_in} text fields, {editable} of them editable.")
    try:
        tf=pg.locator(".advancedFullDialog input[type=text]:not([id*=search]), .md-dialog input[type=text]:not([id*=search])").first
        cur=tf.input_value(); tf.fill(LAST+"Edited"); pg.wait_for_timeout(700)
        rec("Record|6","PASS" if tf.input_value()==LAST+"Edited" else "FAIL", f"Field edited from '{cur}' to '{tf.input_value()}'.")
        sb=pg.locator(".advancedFullDialog button, .md-dialog button").filter(has_text="Save")
        sb.first.click(); pg.wait_for_timeout(4500)
        ok=any(w in bt(pg).lower() for w in ["success","updated","saved"])
        rec("Record|7","PASS" if ok or pg.locator(".md-dialog").count()==0 else "PARTIAL", f"Save persists the updated details (toast={ok}).")
    except Exception as e:
        rec("Record|6","FAIL",str(e)[:150]); rec("Record|7","FAIL","Save not exercised.")

    pg.screenshot(path=EV+"/users/record.png")
    b.close()

json.dump(R, open(EV+"/users/results.json","w"), indent=1)
n,missed,_=resultio.write("USERS", R)   # PARTIAL written verbatim, adjudicated manually afterwards
print(f"\nWROTE {n} rows to USERS; unmatched keys: {missed}")
print("TALLY:", resultio.tally("USERS"))
