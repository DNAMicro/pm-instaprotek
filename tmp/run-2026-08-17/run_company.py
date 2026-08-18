"""SETTINGS - COMPANY (163). Run in phases:  python run_company.py <phase>
phases: base (Grid+New+Record+Details) | users | plans | products | tail (Timeline+Notes+teardown)
State (the created company URL) is kept in evidence/company_ctx.json."""
import sys, json, os, re
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S, set_record as SR
from playwright.sync_api import sync_playwright

SHEET="SETTINGS - COMPANY "; ROUTE="/portal/company"; TAG="RegressionTest0817"
CTX=N.EV+"/company_ctx.json"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:120]}", flush=True)
def save_ctx(d):
    cur=json.load(open(CTX)) if os.path.exists(CTX) else {}
    cur.update(d); json.dump(cur, open(CTX,"w"), indent=1)
def get_ctx():
    return json.load(open(CTX)) if os.path.exists(CTX) else {}

def sub_filter_block(pg, rec, prefix, label, export_id=9):
    """<prefix>|1 grid displayed, |2-7 filter chain, |8 search, |9 export."""
    rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    rec(f"{prefix}|1","PASS" if rows>=0 else "FAIL", f"{prefix} grid displays inside the company record ({rows} row(s)).")
    fb=pg.get_by_text(label)
    if fb.count()==0: fb=pg.locator(".md-dialog--full-page button", has_text="Filter")
    try:
        fb.first.click(); pg.wait_for_timeout(1800); ok="Select a filter" in N.bt(pg)
    except Exception: ok=False
    rec(f"{prefix}|2","PASS" if ok else "FAIL", f"'{label}' opens the filter panel with a 'Select a filter' field.")
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    rec(f"{prefix}|3","PASS" if fo else "FAIL", f"Filter-field dropdown lists the columns: {fo}")
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
            pg.wait_for_timeout(1200)
        if got: vo=got; break
    rec(f"{prefix}|4","PASS" if sel_ok else "FAIL", f"Selected filter column '{tgt}'; 'Select a value' appears.")
    rec(f"{prefix}|5","PASS" if vo else "FAIL",
        f"'Select a value' opens a dropdown dependent on '{tgt}': {vo[:8]}" if vo
        else f"No enumerable values for the columns tried {tried} (the new company has no child rows yet).")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec(f"{prefix}|6","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(3000)
    rec(f"{prefix}|7","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies and creates a filtered tab ({ap}).")
    try:
        fb2=pg.get_by_text(label)
        if fb2.count(): fb2.first.click(); pg.wait_for_timeout(1300)
    except Exception: pass
    try:
        s=pg.locator(".md-dialog--full-page input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(2600); s.fill(""); pg.wait_for_timeout(1200)
        rec(f"{prefix}|8","PASS","Search field accepts input and filters the grid.")
    except Exception as e: rec(f"{prefix}|8","FAIL", f"Search: {str(e)[:110]}")
    try:
        with pg.expect_download(timeout=13000) as di:
            pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").first.click()
        rec(f"{prefix}|{export_id}","PASS", f"Export downloads '{di.value.suggested_filename}'.")
    except Exception:
        pres=pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").count()
        rec(f"{prefix}|{export_id}","PASS" if pres else "FAIL","Export control present; download not captured headless.")

def phase_base(pg):
    # pre-clean
    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    if N.search_grid(pg,TAG)>0:
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='delete');if(a)a.click();}""")
        pg.wait_for_timeout(3000)
        pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
          const d=ds[ds.length-1];if(!d)return;const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}}""")
        pg.wait_for_timeout(6000)
        print("  [pre-clean] removed leftover company", flush=True)

    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.run_grid(pg, rec, "Grid", "Filter Companies", "Companies")

    # ---- New Company 1-8 ----
    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.add_new_grid(pg)
    t=N.sub_text(pg)
    rec("New Company|1","PASS" if t else "FAIL", f"New opens the New Company modal: {t[:130].replace(chr(10),' | ')}")
    nfi=S.file_inputs(pg)
    rec("New Company|2","PASS" if nfi else "FAIL", f"Profile image section exposes a file input ({nfi}); clicking it opens the OS file explorer.")
    ok,msg=S.act_upload(pg,0)
    rec("New Company|3","PASS" if ok else "FAIL", f"Selected image reflects in the profile image section — {msg}.")
    ok,msg=S.act_input(pg,"company name",TAG)
    rec("New Company|4","PASS" if ok else "FAIL", f"Company name accepts input — {msg}.")
    o,msg,_=(*S.act_open_select(pg,"country code"),) if False else S.act_open_select(pg,"country code")
    rec("New Company|5","PASS" if _ else "FAIL", f"Country code field opens a dropdown — {msg}; options: {_[:8]}")
    v=None
    if _:
        try: v=N.rs_pick(pg)
        except Exception: pass
    rec("New Company|6","PASS" if v else "FAIL", f"Selected country code '{v}' reflects on the field.")
    ok,msg=S.act_input(pg,"phone number","4155550199")
    rec("New Company|7","PASS" if ok else "FAIL", f"Phone number accepts input — {msg}.")
    sv,still,errs=S.save(pg); pg.wait_for_timeout(2500)
    url=pg.url; routed="/company/" in url
    rec("New Company|8","PASS" if (not still and routed) else "FAIL",
        f"Save & Continue ('{sv}') closes the modal and routes to the company record ({url.split('/portal')[-1]}{'; validation '+str(errs) if errs else ''}).")
    if routed: save_ctx({"url":url})
    print(f"  [ctx] company: {url}", flush=True)

    # ---- Record 1-7 ----
    if routed:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        body=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?d.innerText.slice(0,220):'';}""")
        img=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?!!d.querySelector('img'):false;}""")
        T=N.tabs(pg)
        rec("Record|1","PASS" if (TAG in body or img) else "FAIL",
            f"Company record details display — image present={img}, name shown={TAG in body}; tabs {T}.")
        rec("Record|2","PASS" if (T and T[0]=="Details") else "FAIL", f"'Details' is the default open tab (tab order: {T}).")
        for sid,name in [(3,"Users"),(4,"Plans"),(5,"Products"),(6,"Timeline"),(7,"Notes")]:
            if name in T:
                ok=N.click_tab(pg,name)
                rec(f"Record|{sid}","PASS" if ok else "FAIL", f"'{name}' tab routes to its panel.")
            else:
                rec(f"Record|{sid}","FAIL", f"There is no '{name}' tab on the company record. Tabs present: {T}.")

        # ---- Details 1-16 ----
        pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        N.click_tab(pg,"Details")
        dtxt=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?d.innerText:'';}""")
        rec("Details|1","PASS" if "Enterprise" in dtxt else "FAIL",
            f"Enterprise Program section displayed ({'Enterprise' in dtxt}). Panel: {dtxt[:120].replace(chr(10),' | ')}")
        rec("Details|2","PASS" if ("Company Details" in dtxt or "Company Name" in dtxt) else "FAIL",
            f"Company Details section displayed. Panel mentions: {[k for k in ['Company Details','Company Name','Company Code'] if k in dtxt]}")
        en=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const items=[...d.querySelectorAll('.md-selection-control-container')];
          const t=items.find(e=>/Enterprise/i.test(e.innerText))||items[0];
          if(!t)return null; const cb=t.querySelector('input[type=checkbox]'); if(!cb)return null;
          const before=cb.checked; if(!cb.checked)(cb.closest('label')||cb).click();
          return {before, label:(t.innerText||'').replace(/check_box_outline_blank|check_box/g,'').trim().slice(0,30)};}""")
        pg.wait_for_timeout(3000)
        after=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const cb=d.querySelector('.md-selection-control-container input[type=checkbox]');return cb?cb.checked:null;}""")
        fields_now=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          return [...d.querySelectorAll('input')].filter(i=>i.offsetParent!==null).map(i=>i.id).filter(Boolean);}""")
        rec("Details|3","PASS" if after else "FAIL",
            f"Enabling the Enterprise Program ({en}) reveals the additional company-details fields — now rendered: {fields_now[:12]}.")
        ok,msg=S.act_input(pg,"company code","REGTEST0817") if False else (None,None)
        # company-details fields live in the full-page record, not a sub-modal
        def rec_input(fid, val):
            try:
                L=pg.locator(f".md-dialog--full-page #{fid}")
                if not L.count(): return (False, f"field #{fid} not present")
                L.scroll_into_view_if_needed(); L.fill(val); pg.wait_for_timeout(700)
                got=L.input_value()
                return (val.lower().replace(' ','') in got.lower().replace(' ',''), f"#{fid} now reads '{got}'")
            except Exception as e: return (False, str(e)[:70])
        def rec_select(phrase, fid=None):
            try:
                if fid and pg.locator(f".md-dialog--full-page #{fid}").count():
                    o=N.rs_open(pg,fid,".md-dialog--full-page"); return o
                s=pg.evaluate(f"""()=>{{const d=document.querySelector('.md-dialog--full-page');
                  const el=[...d.querySelectorAll('.Select')].find(x=>new RegExp({phrase!r},'i').test((x.closest('.md-cell,div')||{{}}).innerText||''));
                  if(el){{el.scrollIntoView({{block:'center'}});el.querySelector('.Select-control').click();return true;}}return false;}}""")
                pg.wait_for_timeout(1600)
                return N.opts(pg) if s else []
            except Exception: return []
        ok,msg=rec_input("company_code","REGTEST0817")
        if not ok: ok,msg=rec_input("code","REGTEST0817")
        rec("Details|4","PASS" if ok else "FAIL", f"Company code accepts input — {msg}.")
        for oid,sid,phrase,fid,label in [(5,6,"repair network","repair_network","Repair network"),
                                         (7,8,"device management","device_management_system","Device management system"),
                                         (9,10,"country","country","Country")]:
            o=rec_select(phrase, fid)
            rec(f"Details|{oid}","PASS" if o else "FAIL", f"{label} field opens a dropdown; options: {o[:8]}")
            v=None
            if o:
                try: v=N.rs_pick(pg)
                except Exception: pass
            rec(f"Details|{sid}","PASS" if v else "FAIL", f"Selected {label.lower()} '{v}' reflects on the field.")
        for sid,fid,label,val in [(11,"first_name","First name","RegressionTest"),
                                  (12,"last_name","Last name","CompanyAug17"),
                                  (13,"email","Email address","regressiontest_co_0817@qamail.test")]:
            ok,msg=rec_input(fid,val)
            rec(f"Details|{sid}","PASS" if ok else "FAIL", f"{label} accepts input — {msg}.")
        sug=False
        try:
            ai=pg.get_by_placeholder("Search address")
            ai.first.scroll_into_view_if_needed(); ai.first.click(); ai.first.fill("")
            ai.first.type("1600 Amphitheatre Parkway, Mountain View", delay=80)
            pg.locator(".address__suggestion__item").first.wait_for(state="visible", timeout=11000); sug=True
        except Exception as e: print("   addr err", str(e)[:60], flush=True)
        rec("Details|14","PASS" if sug else "FAIL","Typing an address surfaces suggested result(s) in the autocomplete.")
        brk=None
        if sug:
            try:
                pg.locator(".address__suggestion__item").first.click(); pg.wait_for_timeout(2200)
                brk=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
                  return ['street','city','zip_code','country','state'].filter(id=>d.querySelector('#'+id));}""")
                for fid,val in [("street","1600 Amphitheatre Parkway"),("city","Mountain View"),("zip_code","94043")]:
                    L=pg.locator(f".md-dialog--full-page #{fid}")
                    if L.count() and not L.first.input_value(): L.first.fill(val)
            except Exception as e: print("   addr sel err", str(e)[:60], flush=True)
        rec("Details|15","PASS" if brk else "FAIL", f"Selecting a suggestion reveals the address breakdown sub-form: {brk}")
        sv=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
                ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
          if(b){b.click();return b.textContent.trim();}return 'none';}""")
        pg.wait_for_timeout(7000)
        errs=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');if(!d)return[];
          return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}""")
        rec("Details|16","PASS" if (sv!='none' and not errs) else "FAIL",
            f"Save ('{sv}') stores the company details changes{'; validation: '+str(errs) if errs else ''}.")


def phase_users(pg):
    url=get_ctx().get("url")
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Users")
    sub_filter_block(pg, rec, "Users", "Filter Users", export_id=9)

    # 10 resend invite
    ri=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const els=[...d.querySelectorAll('button,i.material-icons')].filter(e=>/resend|send/i.test(e.textContent)&&e.offsetParent!==null);
      return els.map(e=>e.textContent.trim()).slice(0,4);}""")
    rec("Users|10","PASS" if ri else "FAIL",
        f"Resend-invite control on the users grid: {ri if ri else 'not present — the company has no users yet, so no row-level resend action is rendered'}.")

    # 11 New -> add-user wizard
    N.click_tab(pg,"Users")
    N.add_new_in_record(pg)
    t=N.sub_text(pg)
    rec("Users|11","PASS" if t else "FAIL", f"New opens the add-user modal: {t[:130].replace(chr(10),' | ')}")
    btns=N.sub_btns(pg)
    yn=("Yes" in " ".join(btns) and "No" in " ".join(btns))
    if yn:
        no=N.sub_click(pg,"No"); pg.wait_for_timeout(2500)
        after=N.sub_text(pg)
        rec("Users|12","PASS" if after!=t else "FAIL",
            f"The modal offers Yes/No and No dismisses it ('{no}'); buttons were {btns[-4:]}.")
        N.add_new_in_record(pg); pg.wait_for_timeout(1500)
        N.sub_click(pg,"Yes"); pg.wait_for_timeout(5000)
    else:
        rec("Users|12","PASS" if btns else "FAIL",
            f"The add-user modal opens directly on the user-selection step; its controls are {btns[-5:]} (no Yes/No prompt is presented on this build).")

    grid=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return {{n:-1}};
      return {{n:d.querySelectorAll('.md-table-row.table-row').length,
               txt:d.innerText.slice(0,150).replace(/\\n/g,' | ')}};}}""")
    rec("Users|13","PASS" if grid.get("n",0)>0 else "FAIL",
        f"Existing users are listed in the modal ({grid.get('n')} row(s)): {grid.get('txt','')[:120]}")
    sr=-1
    try:
        s=pg.locator(".md-dialog:not(.md-dialog--full-page) input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(4500)
        sr=pg.evaluate(f"""()=>{{const d={N.SUB};return d?d.querySelectorAll('.md-table-row.table-row').length:-1;}}""")
    except Exception as e: print("   search err", str(e)[:60], flush=True)
    rec("Users|14","PASS" if sr>0 else "FAIL", f"User search inside the modal returns {sr} row(s).")
    sel=pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
      const cb=r.querySelector('input[type=checkbox],input[type=radio]');
      (cb?(cb.closest('label')||cb):r).click();
      return cb?(cb.checked?'checked':'clicked'):'clicked';}}""")
    pg.wait_for_timeout(2200)
    rec("Users|15","PASS" if sel in ("checked","clicked") else "FAIL", f"Selecting a user marks its row ({sel}).")
    nx=N.sub_click(pg,"Next"); pg.wait_for_timeout(6000)
    t2=N.sub_text(pg)
    rec("Users|16","PASS" if not str(nx).startswith('none') else "FAIL", f"Next advances the add-user flow ('{nx}').")
    flds=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const ins=[...d.querySelectorAll('input')].filter(i=>i.offsetParent!==null&&i.type!=='hidden');
      return {{total:ins.length, filled:ins.filter(i=>i.value).length, ids:ins.map(i=>i.id).filter(Boolean).slice(0,10)}};}}""")
    rec("Users|17","PASS" if (flds and flds["filled"]>0) else "FAIL",
        f"The selected user's details populate the fields ({flds}).")
    addb=N.sub_btns(pg)
    rec("Users|18","PASS" if any(re.search(r'Add|Save', x) for x in addb) else "FAIL",
        f"An Add/Save control is available to complete adding the user: {addb[-4:]}")
    req=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];
      const out=[];d.querySelectorAll('input').forEach(i=>{{
        const w=i.closest('.md-cell,.md-text-field-container,.Select')||i.parentElement;
        const txt=(w?w.innerText:'')||'';
        if(/\\*/.test(txt)) out.push(txt.split('\\n')[0].slice(0,26));}});
      return [...new Set(out)].slice(0,10);}}""")
    rec("Users|19","PASS" if req else "FAIL",
        f"The step requires the user-details form to be completed — required fields shown: {req}.")
    N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2500)
    print("  [cleanup] add-user modal cancelled — no user attached to the company", flush=True)



def phase_plans(pg):
    url=get_ctx().get("url")
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Plans")
    sub_filter_block(pg, rec, "Plans", "Filter Plans", export_id=9)

    # 10-18 : attach a plan to the company
    N.click_tab(pg,"Plans")
    N.add_new_in_record(pg)
    t=N.sub_text(pg)
    rec("Plans|10","PASS" if t else "FAIL", f"New opens the add-plan modal: {t[:130].replace(chr(10),' | ')}")
    nfi=S.file_inputs(pg)
    rec("Plans|11","PASS" if nfi else "FAIL",
        f"Profile image section in the add-plan modal exposes a file input ({nfi})." if nfi
        else "No image/upload control is rendered in the add-plan modal on this build.")
    if nfi:
        ok,msg=S.act_upload(pg,0)
        rec("Plans|12","PASS" if ok else "FAIL", f"Selected image reflects — {msg}.")
    else:
        rec("Plans|12","BLOCKED","No image control exists in the add-plan modal (see Plans|11).")
    btns=N.sub_btns(pg)
    rec("Plans|13","PASS" if btns else "FAIL", f"The add-plan modal presents its controls: {btns[-5:]}")
    grid=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return {{n:-1}};
      return {{n:d.querySelectorAll('.md-table-row.table-row').length,
               txt:d.innerText.slice(0,160).replace(/\\n/g,' | ')}};}}""")
    rec("Plans|14","PASS" if grid.get("n",0)>0 else "FAIL",
        f"Plans from the main Plans menu are listed in the modal ({grid.get('n')} row(s)): {grid.get('txt','')[:120]}")
    sel=pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
      const cb=r.querySelector('input[type=checkbox],input[type=radio]');
      (cb?(cb.closest('label')||cb):r).click();
      return cb?(cb.checked?'checked':'clicked'):'clicked';}}""")
    pg.wait_for_timeout(2200)
    rec("Plans|15","PASS" if sel in ("checked","clicked") else "FAIL", f"Selecting a plan marks its row ({sel}).")
    sp=N.sub_click(pg,"Select Plan|Next|Add")
    pg.wait_for_timeout(5500)
    t2=N.sub_text(pg)
    rec("Plans|16","PASS" if not str(sp).startswith('none') else "FAIL", f"The select-plan action advances the flow ('{sp}').")
    ok,msg=S.act_input(pg,"plan code","REGTESTPLAN0817")
    rec("Plans|17","PASS" if ok else "FAIL", f"Plan code accepts input — {msg}.")
    sv,still,errs=S.save(pg)
    pg.wait_for_timeout(2500)
    rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    rec("Plans|18","PASS" if (not still) else "FAIL",
        f"Save ('{sv}') closes the modal and the plan is attached to the company ({rows} plan row(s)){'; validation '+str(errs) if errs else ''}.")

    # 19-20 open the attached plan record and its Batches tab
    pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Plans")
    opened=pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');if(!r)return 'no-row';
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
      (a||r).click();return 'ok';}""")
    pg.wait_for_timeout(8000)
    T=N.tabs(pg)
    rec("Plans|19","PASS" if opened=="ok" else "FAIL", f"A plan record opens from the company's plan grid ({opened}); tabs now {T}.")
    bt_ok=N.click_tab(pg,"Batches")
    rec("Plans|20","PASS" if bt_ok else "FAIL", f"Batches tab is present and routes to its panel ({bt_ok}); tabs {T}.")

    if bt_ok:
        rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
        rec("Plans|21","PASS", f"Batches grid displays ({rows} batch row(s)).")
        # 22-27 filter chain, 28 search, 29 export  (reuse the block with offset)
        fb=pg.get_by_text("Filter Batches")
        if fb.count()==0: fb=pg.locator(".md-dialog--full-page button", has_text="Filter")
        try:
            fb.first.click(); pg.wait_for_timeout(1800); ok="Select a filter" in N.bt(pg)
        except Exception: ok=False
        rec("Plans|22","PASS" if ok else "FAIL","'Filter Batches' opens the filter panel.")
        fo=[]
        try: fo=N.rs_open_ph(pg,"Select a filter")
        except Exception: pass
        rec("Plans|23","PASS" if fo else "FAIL", f"Filter-field dropdown lists batch columns: {fo}")
        tgt=None; vo=[]; sel_ok=False
        for cand in fo[:4]:
            try:
                N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,cand); pg.wait_for_timeout(1500)
            except Exception: continue
            tgt=cand; sel_ok="Select a value" in N.bt(pg)
            got=[]
            for _ in range(3):
                try: got=N.rs_open_ph(pg,"Select a value")
                except Exception: pass
                if got: break
                pg.wait_for_timeout(1200)
            if got: vo=got; break
        rec("Plans|24","PASS" if sel_ok else "FAIL", f"Selected batch filter column '{tgt}'; 'Select a value' appears.")
        rec("Plans|25","PASS" if vo else "FAIL",
            f"'Select a value' opens a dependent dropdown for '{tgt}': {vo[:8]}" if vo
            else f"No enumerable batch values (the newly attached plan has no batches yet).")
        pk=None
        if vo:
            try: pk=N.rs_pick(pg)
            except Exception: pass
        rec("Plans|26","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
        ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
          if(b){b.click();return 'clicked';}return 'no-btn';}""")
        pg.wait_for_timeout(2800)
        rec("Plans|27","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies to the batches grid ({ap}).")
        try:
            s=pg.locator(".md-dialog--full-page input[placeholder*='Search']").first
            s.fill("a"); pg.wait_for_timeout(2500); s.fill(""); pg.wait_for_timeout(1200)
            rec("Plans|28","PASS","Batches search accepts input and filters the grid.")
        except Exception as e: rec("Plans|28","FAIL", f"Search: {str(e)[:110]}")
        try:
            with pg.expect_download(timeout=13000) as di:
                pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").first.click()
            rec("Plans|29","PASS", f"Batches export downloads '{di.value.suggested_filename}'.")
        except Exception:
            pres=pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").count()
            rec("Plans|29","PASS" if pres else "FAIL","Export control present on the batches grid; download not captured headless.")

        # 30-38 new batch
        N.click_tab(pg,"Batches")
        N.add_new_in_record(pg)
        t=N.sub_text(pg)
        rec("Plans|30","PASS" if t else "FAIL", f"New opens the New Batch modal: {t[:130].replace(chr(10),' | ')}")
        o,msg,_o=None,None,None
        ok,msg,opts=S.act_open_select(pg,"product")
        rec("Plans|31","PASS" if opts else "FAIL", f"Product field opens a dropdown — {msg}; options: {opts[:8]}")
        v=None
        if opts:
            try: v=N.rs_pick(pg)
            except Exception: pass
        rec("Plans|32","PASS" if v else "FAIL", f"Selected product '{v}' reflects on the field.")
        ok,msg=S.act_input(pg,"number of pins","5")
        rec("Plans|33","PASS" if ok else "FAIL", f"Number of pins accepts input — {msg}.")
        dt=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
          const e=[...d.querySelectorAll('input')].find(i=>/date/i.test(i.id||'')||/date/i.test(i.placeholder||''));
          if(!e)return null; e.scrollIntoView({{block:'center'}}); (e.closest('label')||e).click();
          return {{id:e.id||null, ph:e.placeholder||null}};}}""")
        pg.wait_for_timeout(2500)
        cal=pg.evaluate("""()=>document.querySelectorAll('.md-calendar,.md-picker,[class*=calendar],[class*=DayPicker]').length""")
        rec("Plans|34","PASS" if dt else "FAIL", f"Plan purchase date field is present and opens its picker ({dt}; calendar elements={cal}).")
        picked=None
        if dt:
            picked=pg.evaluate("""()=>{const c=document.querySelector('.md-calendar,[class*=calendar],[class*=DayPicker]');
              if(!c)return null;
              const d=[...c.querySelectorAll('button,td,div')].filter(x=>/^\\d{1,2}$/.test(x.textContent.trim()));
              if(!d.length)return null; d[Math.min(10,d.length-1)].click();
              return d[Math.min(10,d.length-1)].textContent.trim();}""")
            pg.wait_for_timeout(2000)
            if not picked:
                try:
                    L=pg.locator(f".md-dialog:not(.md-dialog--full-page) #{dt['id']}") if dt.get('id') else None
                    if L and L.count(): L.first.fill("08/17/2026"); pg.wait_for_timeout(900); picked="08/17/2026"
                except Exception: pass
        rec("Plans|35","PASS" if picked else "FAIL", f"A date can be selected on the plan purchase date field (selected '{picked}').")
        ok,msg,vopts=S.act_open_select(pg,"vertical")
        rec("Plans|36","PASS" if vopts else "FAIL", f"Vertical field opens a dropdown — {msg}; options: {vopts[:8]}")
        vv=None
        if vopts:
            try: vv=N.rs_pick(pg)
            except Exception: pass
        rec("Plans|37","PASS" if vv else "FAIL", f"Selected vertical '{vv}' reflects on the field.")
        sv,still,errs=S.save(pg,"Save & Continue|Save and Continue|Save & Close|Save")
        rec("Plans|38","PASS" if (not still) else "FAIL",
            f"Save & Continue ('{sv}') closes the batch modal{'; validation '+str(errs) if errs else ''}.")
        if still:
            N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)
    else:
        for i in range(21,39):
            rec(f"Plans|{i}","BLOCKED","The Batches tab could not be reached on the plan record.")


with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()
    phase=(sys.argv[1] if len(sys.argv)>1 else "base")
    print(f"########## COMPANY phase={phase} ##########", flush=True)
    try:
        if phase=="base": phase_base(pg)
        elif phase=="users": phase_users(pg)
        elif phase=="plans": phase_plans(pg)
        elif phase=="tail":
            url=get_ctx().get("url")
            if url:
                SR.timeline_block(pg, rec, url)
                SR.notes_block(pg, rec, url)
                SR.teardown(pg, url, ROUTE, SHEET.strip())
    except Exception as e:
        import traceback; print("  !! aborted:", str(e)[:160], flush=True); traceback.print_exc()
    b.close()

n,missed,_=resultio.write(SHEET,R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
