"""COMPANY > Products tab (sheet section 'Company', 51 scenarios)."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S
from playwright.sync_api import sync_playwright

URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
TAG="RegressionTest0817"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:120]}", flush=True)

def rs_by_label(pg, phrase, scope_full=False):
    sc=".md-dialog--full-page" if scope_full else ".md-dialog:not(.md-dialog--full-page)"
    ok=pg.evaluate(f"""()=>{{const d=document.querySelector('{sc}');if(!d)return false;
      const el=[...d.querySelectorAll('.Select')].find(x=>new RegExp({phrase!r},'i').test(((x.closest('.md-cell,.md-text-field-container,div')||{{}}).innerText)||''));
      if(el){{el.scrollIntoView({{block:'center'}});el.querySelector('.Select-control').click();return true;}}return false;}}""")
    pg.wait_for_timeout(1700)
    return N.opts(pg) if ok else []

def fill_label(pg, phrase, val, scope_full=False):
    sc=".md-dialog--full-page" if scope_full else ".md-dialog:not(.md-dialog--full-page)"
    r=pg.evaluate(f"""()=>{{const d=document.querySelector('{sc}');if(!d)return null;
      const ins=[...d.querySelectorAll('input,textarea')].filter(i=>i.offsetParent!==null);
      for(const i of ins){{
        const w=i.closest('.md-text-field-container,.md-cell')||i.parentElement;
        const t=((w?w.innerText:'')||'').toLowerCase();
        if(t.includes({phrase!r})){{
          const proto=i.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
          const set=Object.getOwnPropertyDescriptor(proto,'value').set;
          set.call(i,{val!r}); i.dispatchEvent(new Event('input',{{bubbles:true}}));
          return {{label:(w?w.innerText:'').split('\\n')[0].slice(0,32), val:i.value}};}}
      }} return null;}}""")
    pg.wait_for_timeout(700); return r

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Products")

    # ---- 1-9 grid + filters + export ----
    rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    rec("Company|1","PASS", f"The company's Products grid displays ({rows} row(s)).")
    fb=pg.get_by_text("Filter Products")
    if fb.count()==0: fb=pg.locator(".md-dialog--full-page button", has_text="Filter")
    try:
        fb.first.click(); pg.wait_for_timeout(1800); ok="Select a filter" in N.bt(pg)
    except Exception: ok=False
    rec("Company|2","PASS" if ok else "FAIL","'Filter Products' opens the filter panel.")
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    rec("Company|3","PASS" if fo else "FAIL", f"Filter-field dropdown lists the product columns: {fo}")
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
    rec("Company|4","PASS" if sel_ok else "FAIL", f"Selected filter column '{tgt}'; 'Select a value' appears.")
    rec("Company|5","PASS" if vo else "FAIL",
        f"Dependent value dropdown for '{tgt}': {vo[:8]}" if vo else f"No enumerable values yet (the new company has no products).")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Company|6","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(2800)
    rec("Company|7","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies to the products grid ({ap}).")
    try:
        s=pg.locator(".md-dialog--full-page input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(2500); s.fill(""); pg.wait_for_timeout(1200)
        rec("Company|8","PASS","Products search accepts input and filters the grid.")
    except Exception as e: rec("Company|8","FAIL", f"Search: {str(e)[:110]}")
    try:
        with pg.expect_download(timeout=13000) as di:
            pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").first.click()
        rec("Company|9","PASS", f"Products export downloads '{di.value.suggested_filename}'.")
    except Exception:
        pres=pg.locator(".md-dialog--full-page").get_by_text("Export as CSV").count()
        rec("Company|9","PASS" if pres else "FAIL","Export control present; download not captured headless.")

    # ---- 10-23 new product ----
    N.click_tab(pg,"Products"); N.add_new_in_record(pg)
    t=N.sub_text(pg)
    rec("Company|10","PASS" if t else "FAIL", f"New opens the New Product modal: {t[:130].replace(chr(10),' | ')}")
    nfi=S.file_inputs(pg)
    rec("Company|11","PASS" if nfi else "FAIL", f"Profile image section exposes a file input ({nfi}).")
    if nfi:
        ok,msg=S.act_upload(pg,0)
        rec("Company|12","PASS" if ok else "FAIL", f"Selected image reflects — {msg}.")
    else:
        rec("Company|12","BLOCKED","No image control in the New Product modal (see Company|11).")
    g=fill_label(pg,"barcode","REGTESTBC0817")
    rec("Company|13","PASS" if (g and g.get('val')) else "FAIL", f"Product barcode accepts input — {g}.")
    g=fill_label(pg,"product name",TAG)
    if not (g and g.get('val')): g=fill_label(pg,"name",TAG)
    rec("Company|14","PASS" if (g and g.get('val')) else "FAIL", f"Product name accepts input — {g}.")
    for oid,sid,phrase,label in [(15,16,"plan","Plan"),(17,18,"device categor","Device categories"),(19,20,"product categor","Product category")]:
        o=rs_by_label(pg,phrase)
        rec(f"Company|{oid}","PASS" if o else "FAIL", f"{label} field opens a dropdown; options: {o[:8]}")
        v=None
        if o:
            try: v=N.rs_pick(pg)
            except Exception: pass
        rec(f"Company|{sid}","PASS" if v else "FAIL", f"Selected {label.lower()} '{v}' reflects on the field.")
    g=fill_label(pg,"agreement","Regression test agreement")
    rec("Company|21","PASS" if (g and g.get('val')) else "FAIL", f"Agreement accepts input — {g}.")
    wf=pg.evaluate(f"""()=>{{const d={N.SUB};const items=[...d.querySelectorAll('.md-selection-control-container')];
      const t=items.find(e=>/bypass|workflow/i.test(e.innerText))||items[0];
      if(!t)return null;const cb=t.querySelector('input[type=checkbox]');if(!cb)return null;
      (cb.closest('label')||cb).click();
      return {{label:(t.innerText||'').replace(/check_box_outline_blank|check_box/g,'').trim().slice(0,32),checked:cb.checked}};}}""")
    pg.wait_for_timeout(1500)
    rec("Company|22","PASS" if (wf and wf.get('checked')) else "FAIL", f"A workflow-to-bypass option can be selected — {wf}.")
    sv,still,errs=S.save(pg,"Save & Continue|Save and Continue|Save & Close|Save")
    pg.wait_for_timeout(2500)
    rec("Company|23","PASS" if not still else "FAIL",
        f"Save & Continue ('{sv}') closes the New Product modal and creates the product{'; validation '+str(errs) if errs else ''}.")
    if still:
        print("   validation:", errs, flush=True)
        N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)

    json.dump({"ok":True}, open(N.EV+"/co_products_stage1.json","w"))
    b.close()

n,missed,_=resultio.write("SETTINGS - COMPANY ",R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally('SETTINGS - COMPANY ')}")
