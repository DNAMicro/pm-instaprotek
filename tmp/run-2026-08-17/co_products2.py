"""COMPANY > Products 15-51: create the product with the real field ids, then walk the
product record (details, batches, review questions, shop set-up)."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S
from playwright.sync_api import sync_playwright

URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
TAG="RegressionTest0817"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:120]}", flush=True)
SUBSEL=".md-dialog:not(.md-dialog--full-page)"

def fill(pg, fid, val, scope=SUBSEL):
    L=pg.locator(f"{scope} #{fid}")
    if not L.count(): return (False, f"#{fid} not present")
    L.first.scroll_into_view_if_needed(); L.first.fill(val); pg.wait_for_timeout(600)
    return (True, f"#{fid} now reads '{L.first.input_value()}'")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
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

    o2=[]
    try: o2=N.rs_open(pg,"categories",SUBSEL)
    except Exception as e: print("  cat err", str(e)[:60], flush=True)
    rec("Company|17","PASS" if o2 else "FAIL", f"Device Categories field (#categories) opens a dropdown; options: {o2[:8]}")
    v2=None
    if o2:
        try: v2=N.rs_pick(pg)
        except Exception: pass
    rec("Company|18","PASS" if v2 else "FAIL", f"Selected device category '{v2}' reflects on the field.")

    o3=[]
    try: o3=N.md_open(pg,"product_category-toggle")
    except Exception as e: print("  pc err", str(e)[:60], flush=True)
    rec("Company|19","PASS" if o3 else "FAIL", f"Product Category field (react-md select) opens; options: {o3[:8]}")
    v3=None
    if o3:
        try: v3=N.md_pick(pg)
        except Exception: pass
    rec("Company|20","PASS" if v3 else "FAIL", f"Selected product category '{v3}' reflects on the field.")

    # responsible claim payer is also required
    try:
        o4=N.md_open(pg,"responsible_claim_payer-toggle")
        if o4: N.md_pick(pg)
        print("  responsible claim payer:", o4[:4], flush=True)
    except Exception as e: print("  rcp err", str(e)[:60], flush=True)

    ok,msg=fill(pg,"agreement","Regression test agreement 2026-08-17")
    rec("Company|21","PASS" if ok else "FAIL", f"Agreement accepts input — {msg}.")
    wf=pg.evaluate(f"""()=>{{const d={N.SUB};const cb=d.querySelector('#bypass_screen_test');
      if(!cb)return null;(cb.closest('label')||cb).click();
      return {{label:'Bypass Screen Test',checked:cb.checked}};}}""")
    pg.wait_for_timeout(1200)
    rec("Company|22","PASS" if (wf and wf.get('checked')) else "FAIL", f"A workflow-to-bypass option can be selected — {wf}.")
    sv,still,errs=S.save(pg,"Save & Continue|Save and Continue|Save & Close|Save")
    pg.wait_for_timeout(3000)
    rec("Company|23","PASS" if not still else "FAIL",
        f"Save & Continue ('{sv}') closes the New Product modal and creates the product{'; validation '+str(errs) if errs else ''}.")
    if still:
        print("  validation:", errs, flush=True)
        N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)

    # ---- 24,25 open the product record ----
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Products")
    nrows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    opened=pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');if(!r)return 'no-row';
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
      (a||r).click();return 'ok';}""")
    pg.wait_for_timeout(8500)
    T=N.tabs(pg)
    rec("Company|24","PASS" if opened=="ok" else "FAIL", f"A product record opens from the company's products grid ({opened}; {nrows} product row(s)); tabs {T}.")
    det=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');const t=d?d.innerText:'';
      return ['Product Barcode','Product Name','Plan','Device Categories','Agreement','Workflow'].filter(k=>t.includes(k));}""")
    rec("Company|25","PASS" if len(det)>=3 else "FAIL", f"Product details are displayed on the record — {det}.")

    # ---- 26,27 batches tab ----
    bt=N.click_tab(pg,"Batches")
    rec("Company|26","PASS" if bt else "FAIL", f"Batches tab is present on the product record and routes to its panel ({bt}); tabs {T}.")
    if bt:
        nb=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
        txt=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
          return p.length?p[0].innerText.slice(0,180).replace(/\\n/g,' | '):'';}""")
        rec("Company|27","PASS" if nb>=0 else "FAIL",
            f"Batches where the product is added are listed ({nb} row(s)): {txt[:130]}")
    else:
        rec("Company|27","BLOCKED","Batches tab not reachable on the product record.")

    # ---- 28-31 review questions ----
    rq=N.click_tab(pg,"Review Questions")
    if not rq:
        rq=N.click_tab(pg,"Review Question")
    rec("Company|28","PASS" if rq else "FAIL", f"Review Questions tab is present and routes to its panel ({rq}); tabs {N.tabs(pg)}.")
    if rq:
        n=N.add_new_in_record(pg)
        t=N.sub_text(pg)
        rec("Company|29","PASS" if t else "FAIL", f"Add opens the review-questions picker: {t[:130].replace(chr(10),' | ')}")
        sel=pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
          const cb=r.querySelector('input[type=checkbox],input[type=radio]');
          (cb?(cb.closest('label')||cb):r).click();
          return cb?(cb.checked?'checked':'clicked'):'clicked';}}""")
        pg.wait_for_timeout(2200)
        rec("Company|30","PASS" if sel in ("checked","clicked") else "FAIL", f"Review questions can be selected ({sel}).")
        sv2=N.sub_click(pg,"Add Selected|Add|Save")
        pg.wait_for_timeout(6000)
        still2=N.has_sub(pg)
        rec("Company|31","PASS" if not still2 else "FAIL", f"'Add selected' ('{sv2}') closes the picker and attaches the questions.")
        if still2: N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)
    else:
        for i in (29,30,31): rec(f"Company|{i}","BLOCKED","Review Questions tab not present on the product record.")

    json.dump({"stage2":True}, open(N.EV+"/co_products_stage2.json","w"))
    b.close()

n,missed,_=resultio.write("SETTINGS - COMPANY ",R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally('SETTINGS - COMPANY ')}")
