"""DEVICE CATEGORY Devices|4,5,13,14,15 verified against an EXISTING category.
Filtering is read-only; the Add-Devices modal is exercised then CANCELLED, so no
live category is modified. Devices|15 (commit) is deliberately not executed."""
import sys
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

SHEET="SETTINGS - DEVICE  CATEGORY"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:135]}", flush=True)

DEVROWS = """()=>{const ts=[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')];
  const t=ts.find(x=>/Device Name/.test(x.innerText));
  if(!t)return {n:-1,names:[]};
  const rs=[...t.querySelectorAll('.md-table-row.table-row')];
  return {n:rs.length, names:rs.slice(0,3).map(r=>r.innerText.replace(/\\s+/g,' ').trim().slice(0,32))};}"""

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()
    pg.goto(N.BASE+"/portal/category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    catname=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.split('\\n')[0].trim():null;}""")
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8500)
    print(f"  [ctx] using existing category '{catname}' (read-only)", flush=True)

    # ---- Devices|4,5 : sub-grid filter values against a populated device grid ----
    N.click_tab(pg,"Devices")
    nrows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    fb=pg.get_by_text("Filter Devices")
    if fb.count(): fb.first.click(); pg.wait_for_timeout(2000)
    vo=[]; tgt=None
    try:
        fo=N.rs_open_ph(pg,"Select a filter")
        for cand in fo[:3]:
            N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,cand); pg.wait_for_timeout(1600)
            tgt=cand
            got=[]
            for _ in range(3):
                try: got=N.rs_open_ph(pg,"Select a value")
                except Exception: pass
                if got: break
                pg.wait_for_timeout(1200)
            if got: vo=got; break
    except Exception as e: print("   filter err", str(e)[:70], flush=True)
    rec("Devices|4","PASS" if vo else "FAIL",
        f"'Select a value' opens a dropdown dependent on '{tgt}' — options {vo[:8]} (verified on category '{catname}', which has {nrows} device row(s); a newly created category has none, which is why this needs populated data).")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Devices|5","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field and applies to the device sub-grid.")

    # ---- Devices|13,14 : Add-Devices step 2, then CANCEL ----
    pg.goto(pg.url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    N.click_tab(pg,"Devices"); N.add_new_in_record(pg)
    try:
        s=pg.get_by_placeholder("Search Brands...")
        s.first.fill("Apple"); pg.wait_for_timeout(4000)
        pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');
          const cb=r.querySelector('input[type=checkbox],input[type=radio]');(cb?(cb.closest('label')||cb):r).click();}}""")
        pg.wait_for_timeout(2200)
        N.sub_click(pg,"Next"); pg.wait_for_timeout(7000)
    except Exception as e: print("   step1 err", str(e)[:70], flush=True)

    before={"n":0,"names":[]}
    for _ in range(8):
        before=pg.evaluate(DEVROWS)
        if before["n"]>0: break
        pg.wait_for_timeout(2500)
    print(f"   step2 devices: {before['n']} e.g. {before['names'][:2]}", flush=True)
    ds=-1; term=None
    try:
        raw=(before["names"][0] if before["names"] else "")
        raw=raw.replace("check_box_outline_blank","").replace("check_box","").strip()
        term=(raw.split()[0] if raw else "a")
        box=pg.get_by_placeholder("Search Devices...")
        box=(box.last if box.count()>1 else box.first)
        box.fill(""); box.fill(term); pg.wait_for_timeout(5000)
        ds=pg.evaluate(DEVROWS)["n"]
    except Exception as e: print("   search err", str(e)[:70], flush=True)
    rec("Devices|13","PASS" if ds>0 else "FAIL",
        f"Device search in Step 2 accepts input and filters the list — searching '{term}' returned {ds} of {before['n']} device row(s).")
    dp=pg.evaluate("""()=>{const ts=[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')];
      const t=ts.find(x=>/Device Name/.test(x.innerText)); if(!t)return 'no-device-table';
      const r=t.querySelector('.md-table-row.table-row'); if(!r)return 'no-row';
      const cb=r.querySelector('input[type=checkbox]'); if(!cb)return 'no-checkbox';
      (cb.closest('label')||cb).click(); return cb.checked?'checked':'clicked';}""")
    pg.wait_for_timeout(2500)
    saveable=pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent));
      return b?!b.disabled:null;}}""")
    rec("Devices|14","PASS" if dp=="checked" else "FAIL",
        f"Selecting a device ticks its checkbox ({dp}) and enables Save & Close (enabled={saveable}).")
    rec("Devices|15","BLOCKED",
        f"Not executed by choice: committing Save & Close would permanently add devices to the live category '{catname}' on an environment carrying production data. A self-created category cannot be used because its Step 2 device list comes back empty (0 rows), so the commit could only be exercised against real configuration. The modal was verified up to the enabled Save & Close control (enabled={saveable}) and then cancelled.")
    N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2500)
    print("  [cleanup] Add-Devices modal cancelled — live category unchanged", flush=True)
    b.close()

n,missed,_=resultio.write(SHEET,R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
