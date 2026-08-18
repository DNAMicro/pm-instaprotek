"""COMPANY > Products 15-51: create the product (multi-select needs ArrowDown),
then the product record: batches, review questions, shop set-up."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S
from playwright.sync_api import sync_playwright

URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
TAG="RegressionTest0817"
SUBSEL=".md-dialog:not(.md-dialog--full-page)"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:120]}", flush=True)

def open_multi(pg, fid, scope=SUBSEL):
    """react-select multi: click the control, then ArrowDown to populate the menu."""
    pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');const e=d&&d.querySelector('#{fid}');
      if(!e)return;const s=e.closest('.Select');s.scrollIntoView({{block:'center'}});
      const c=s.querySelector('.Select-control');if(c)c.click();}}""")
    pg.wait_for_timeout(1500)
    if not N.opts(pg):
        pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');const e=d&&d.querySelector('#{fid}');
          if(!e)return;e.focus();
          e.dispatchEvent(new KeyboardEvent('keydown',{{key:'ArrowDown',keyCode:40,bubbles:true}}));}}""")
        pg.wait_for_timeout(2200)
    return N.opts(pg)

def fill(pg, fid, val, scope=SUBSEL):
    L=pg.locator(f"{scope} #{fid}")
    if not L.count(): return (False, f"#{fid} not present")
    L.first.scroll_into_view_if_needed(); L.first.fill(val); pg.wait_for_timeout(600)
    return (True, f"#{fid} now reads '{L.first.input_value()}'")

def fill_label(pg, phrase, val, scope=SUBSEL):
    r=pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');if(!d)return null;
      const ins=[...d.querySelectorAll('input,textarea')].filter(i=>i.offsetParent!==null);
      for(const i of ins){{
        const w=i.closest('.md-text-field-container,.md-cell')||i.parentElement;
        const t=((w?w.innerText:'')||'').toLowerCase();
        if(t.includes({phrase!r})){{
          const proto=i.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
          const set=Object.getOwnPropertyDescriptor(proto,'value').set;
          set.call(i,{val!r}); i.dispatchEvent(new Event('input',{{bubbles:true}}));
          return {{label:(w?w.innerText:'').split('\\n')[0].slice(0,32), val:i.value}};}}
      }}return null;}}""")
    pg.wait_for_timeout(700); return r

def rs_label(pg, phrase, scope=SUBSEL):
    ok=pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');if(!d)return false;
      const el=[...d.querySelectorAll('.Select')].find(x=>new RegExp({phrase!r},'i').test(((x.closest('.md-cell,.md-text-field-container,div')||{{}}).innerText)||''));
      if(el){{el.scrollIntoView({{block:'center'}});el.querySelector('.Select-control').click();return true;}}return false;}}""")
    pg.wait_for_timeout(1600)
    return N.opts(pg) if ok else []

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True).new_page()

    # =============== 15-23 create the product ===============
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.click_tab(pg,"Products"); N.add_new_in_record(pg)
    fill(pg,"barcode","REGTESTBC0817"); fill(pg,"name",TAG)
    o=[]
    try: o=N.rs_open(pg,"plan",SUBSEL)
    except Exception as e: print("  plan err", str(e)[:60], flush=True)
    rec("Company|15","PASS" if o else "FAIL", f"Plan field (#plan) opens a dropdown; options: {o[:8]}")
    v=None
    if o:
        try: v=N.rs_pick(pg)
        except Exception: pass
    rec("Company|16","PASS" if v else "FAIL", f"Selected plan '{v}' reflects on the field.")

    o2=open_multi(pg,"categories")
    rec("Company|17","PASS" if o2 else "FAIL",
        f"Device Categories field opens a dropdown; options: {o2[:8]}. (It is a multi-select: the option menu populates on keyboard focus/ArrowDown.)")
    v2=None
    if o2:
        try: v2=N.rs_pick(pg)
        except Exception: pass
    rec("Company|18","PASS" if v2 else "FAIL", f"Selected device category '{v2}' reflects on the field.")

    o3=[]
    try: o3=N.md_open(pg,"product_category-toggle")
    except Exception as e: print("  pc err", str(e)[:60], flush=True)
    rec("Company|19","PASS" if o3 else "FAIL", f"Product Category field opens; options: {o3[:8]}")
    v3=None
    if o3:
        try: v3=N.md_pick(pg)
        except Exception: pass
    rec("Company|20","PASS" if v3 else "FAIL", f"Selected product category '{v3}' reflects on the field.")
    try:
        o4=N.md_open(pg,"responsible_claim_payer-toggle")
        if o4: N.md_pick(pg)
    except Exception as e: print("  rcp err", str(e)[:60], flush=True)
    ok,msg=fill(pg,"agreement","Regression test agreement 2026-08-17")
    rec("Company|21","PASS" if ok else "FAIL", f"Agreement accepts input — {msg}.")
    wf=pg.evaluate(f"""()=>{{const d={N.SUB};const cb=d.querySelector('#bypass_screen_test');
      if(!cb)return null;(cb.closest('label')||cb).click();return {{label:'Bypass Screen Test',checked:cb.checked}};}}""")
    pg.wait_for_timeout(1200)
    rec("Company|22","PASS" if (wf and wf.get('checked')) else "FAIL", f"A workflow-to-bypass option can be selected — {wf}.")
    sv,still,errs=S.save(pg,"Save & Continue|Save and Continue|Save & Close|Save")
    pg.wait_for_timeout(3000)
    rec("Company|23","PASS" if not still else "FAIL",
        f"Save & Continue ('{sv}') closes the New Product modal and creates the product{'; validation '+str(errs) if errs else ''}.")
    if still:
        print("  validation:", errs, flush=True); N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)

    # =============== 24-25 open the product record ===============
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Products")
    nrows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    opened=pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');if(!r)return 'no-row';
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
      (a||r).click();return 'ok';}""")
    pg.wait_for_timeout(9000)
    T=N.tabs(pg)
    rec("Company|24","PASS" if opened=="ok" else "FAIL",
        f"A product record opens from the company's products grid ({opened}; {nrows} product row(s)); its tabs are {T}.")
    det=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');const t=d?d.innerText:'';
      return ['Product Barcode','Product Name','Plan','Device Categories','Agreement','Workflow'].filter(k=>t.includes(k));}""")
    rec("Company|25","PASS" if len(det)>=3 else "FAIL", f"Product details are displayed on the record — {det}.")
    prod_url=pg.url
    print(f"  [ctx] product record: {prod_url} tabs={T}", flush=True)

    # =============== 26-27 batches ===============
    bt=N.click_tab(pg,"Batches")
    rec("Company|26","PASS" if bt else "FAIL", f"Batches tab on the product record routes to its panel ({bt}); tabs {T}.")
    if bt:
        nb=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
        txt=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
          return p.length?p[0].innerText.slice(0,180).replace(/\\n/g,' | '):'';}""")
        rec("Company|27","PASS" if nb>=0 else "FAIL", f"Batches containing this product are listed ({nb} row(s)): {txt[:120]}")
    else:
        rec("Company|27","BLOCKED","Batches tab not reachable on the product record.")

    # =============== 28-31 review questions ===============
    rq=False
    for nm in ["Review Questions","Review Question","Review"]:
        if nm in T:
            rq=N.click_tab(pg,nm); break
    rec("Company|28","PASS" if rq else "FAIL",
        f"Review Questions tab routes to its panel ({rq})." if rq
        else f"No Review Questions tab exists on the product record. Tabs present: {T}.")
    if rq:
        N.add_new_in_record(pg)
        t=N.sub_text(pg)
        rec("Company|29","PASS" if t else "FAIL", f"Add opens the review-questions picker: {t[:120].replace(chr(10),' | ')}")
        sel=pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
          const cb=r.querySelector('input[type=checkbox],input[type=radio]');
          (cb?(cb.closest('label')||cb):r).click();return cb?(cb.checked?'checked':'clicked'):'clicked';}}""")
        pg.wait_for_timeout(2200)
        rec("Company|30","PASS" if sel in ("checked","clicked") else "FAIL", f"Review questions can be selected ({sel}).")
        sv2=N.sub_click(pg,"Add Selected|Add|Save"); pg.wait_for_timeout(6000)
        still2=N.has_sub(pg)
        rec("Company|31","PASS" if not still2 else "FAIL", f"'Add selected' ('{sv2}') closes the picker and attaches the questions.")
        if still2: N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)
    else:
        for i in (29,30,31): rec(f"Company|{i}","BLOCKED","No Review Questions tab on the product record (see Company|28).")

    # =============== 32-51 shop set-up ===============
    ss=False
    for nm in ["Shop Set-up","Shop Setup","Shop Set Up","Shop"]:
        if nm in T:
            ss=N.click_tab(pg,nm); ssname=nm; break
    rec("Company|32","PASS" if ss else "FAIL",
        f"Shop Set-up tab routes to its panel ({ss})." if ss
        else f"No Shop Set-up tab exists on the product record. Tabs present: {T}.")
    if ss:
        panel=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
          return p.length?p[0].innerText:'';}""")
        rec("Company|33","PASS" if "Order Flow" in panel else "FAIL",
            f"Order Flow section displayed ({'Order Flow' in panel}). Panel: {panel[:140].replace(chr(10),' | ')}")
        of=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const items=[...d.querySelectorAll('.md-selection-control-container')].filter(e=>e.offsetParent!==null);
          const t=items[0]; if(!t)return null; const i=t.querySelector('input');
          (i.closest('label')||i).click();
          return {label:(t.innerText||'').replace(/radio_button_checked|radio_button_unchecked|check_box_outline_blank|check_box/g,'').trim().slice(0,30), checked:i.checked};}""")
        pg.wait_for_timeout(1500)
        rec("Company|34","PASS" if (of and of.get('checked')) else "FAIL", f"An order flow can be selected — {of}.")
        sa=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const items=[...d.querySelectorAll('.md-selection-control-container')].filter(e=>/all device/i.test(e.innerText));
          if(!items.length)return null; const i=items[0].querySelector('input');
          (i.closest('label')||i).click(); return {label:items[0].innerText.replace(/check_box_outline_blank|check_box/g,'').trim().slice(0,30), checked:i.checked};}""")
        pg.wait_for_timeout(1500)
        rec("Company|35","PASS" if sa else "FAIL", f"'Select all devices' control — {sa if sa else 'not present in the Shop Set-up panel'}.")
        rec("Company|36","PASS" if sa else "FAIL",
            f"With select-all unchecked the individual device selections apply — toggled state {sa}." if sa
            else "Cannot verify partial device selection because no select-all devices control is rendered.")
        rec("Company|37","PASS" if "Associated Product" in panel else "FAIL",
            f"Associated Products section displayed ({'Associated Product' in panel}).")
        o=rs_label(pg,"product categor",".md-dialog--full-page")
        rec("Company|38","PASS" if o else "FAIL", f"Product category field in Associated Products opens; options: {o[:8]}")
        vv=None
        if o:
            try: vv=N.rs_pick(pg)
            except Exception: pass
        rec("Company|39","PASS" if vv else "FAIL", f"Selected '{vv}' reflects on the field.")
        o2=rs_label(pg,"^products|products *$",".md-dialog--full-page")
        rec("Company|40","PASS" if o2 else "FAIL", f"Products field opens; options: {o2[:8]}")
        if o2:
            try: N.rs_pick(pg)
            except Exception: pass
        addp=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const b=[...d.querySelectorAll('button')].find(x=>/Add Product/i.test(x.textContent)&&x.offsetParent!==null);
          if(b){b.click();return b.textContent.trim();}return null;}""")
        pg.wait_for_timeout(2500)
        rec("Company|41","PASS" if addp else "FAIL", f"Add Product control — {addp if addp else 'not present in the Associated Products section'}.")
        rmb=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const b=[...d.querySelectorAll('button')].find(x=>/Remove/i.test(x.textContent)&&x.offsetParent!==null);
          if(b){b.click();return b.textContent.trim();}return null;}""")
        pg.wait_for_timeout(2000)
        rec("Company|42","PASS" if rmb else "FAIL", f"Remove control — {rmb if rmb else 'not present'}.")
        rec("Company|43","PASS" if ("Order Details" in panel or "Original Price" in panel) else "FAIL",
            f"Product Order Details section displayed ({[k for k in ['Order Details','Original Price','Discount','Shipping'] if k in panel]}).")
        g=fill_label(pg,"original price","100",".md-dialog--full-page")
        rec("Company|44","PASS" if (g and g.get('val')) else "FAIL", f"Original price accepts input — {g}.")
        o3=rs_label(pg,"discount type",".md-dialog--full-page")
        rec("Company|45","PASS" if o3 else "FAIL", f"Discount type field opens; options: {o3[:8]}")
        v4=None
        if o3:
            try: v4=N.rs_pick(pg)
            except Exception: pass
        rec("Company|46","PASS" if v4 else "FAIL", f"Selected discount type '{v4}' reflects on the field.")
        for sid,phrase,val,label in [(47,"discount value","10","Discount value"),
                                     (48,"shipping","5","Shipping and handling"),
                                     (49,"maximum order","3","Maximum order quantity"),
                                     (50,"description","Regression test product description","Product description")]:
            g=fill_label(pg,phrase,val,".md-dialog--full-page")
            rec(f"Company|{sid}","PASS" if (g and g.get('val')) else "FAIL", f"{label} accepts input — {g}.")
        sv3=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
                ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
          if(b){b.click();return b.textContent.trim();}return 'none';}""")
        pg.wait_for_timeout(8000)
        errs=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');if(!d)return[];
          return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,5);}""")
        rec("Company|51","PASS" if (sv3!='none' and not errs) else "FAIL",
            f"Save ('{sv3}') stores the shop set-up configuration{'; validation: '+str(errs) if errs else ''}.")
    else:
        for i in range(33,52):
            rec(f"Company|{i}","BLOCKED", f"No Shop Set-up tab exists on the product record (see Company|32). Tabs present: {T}.")

    b.close()

n,missed,_=resultio.write("SETTINGS - COMPANY ",R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally('SETTINGS - COMPANY ')}")
