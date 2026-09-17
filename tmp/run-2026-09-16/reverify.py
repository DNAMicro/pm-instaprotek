"""READ-ONLY re-verification of suspected-artifact failures. Opens records, never writes."""
import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
import importlib.util
spec=importlib.util.spec_from_file_location("slib","/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/settings_lib.py")
slib=importlib.util.module_from_spec(spec); spec.loader.exec_module(slib)
from playwright.sync_api import sync_playwright

OPEN_ONLY={  # sheet -> (route, filter label)
 "SETTINGS - REGIONS":("/portal/regions","Filter Regions"),
 "SETTINGS - SUPPORT":("/portal/support","Filter Support"),
 "SETTINGS - COVERAGE TYPE ":("/portal/coverage-type","Filter Coverage Types"),
 "SETTINGS-REVIEW QUESTIONS":("/portal/review-questions","Filter Review Questions"),
 "SETTINGS - LANGUAGE":("/portal/languages","Filter Languages"),
}
def wait_rows(pg,secs=180):
    for _ in range(int(secs/3)):
        pg.wait_for_timeout(3000)
        n=pg.locator(".md-table-row.table-row").count()
        if n>0: return n
    return 0

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100},accept_downloads=True).new_page()

    # --- Grid|10 record-open on five modules ---
    for sheet,(route,filt) in OPEN_ONLY.items():
        try:
            pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000)
            rows=wait_rows(pg)
            op=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
              (a||r).click();return 'ok';}""") if rows else 'no-row'
            pg.wait_for_timeout(20000)
            shell=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')||document.querySelector('.advancedFullDialog')||document.querySelector('.md-dialog');
              return d?d.innerText.slice(0,200).replace(/\\s+/g,' '):'';}""")
            st="PASS" if shell else "FAIL"
            note=(f"Re-verified read-only {('with %d rows rendered'%rows)}: clicking a grid record opens its record view ({op}). "
                  f"Header: {shell[:120]}") if shell else f"Record did not open (rows={rows}, {op})."
            n,_,_=resultio.write(sheet, {"Grid|10":(st,note)})
            print(f"  {sheet:32s} rows={rows:3d} -> Grid|10 {st}", flush=True)
        except Exception as e:
            print(f"  {sheet:32s} ERR {str(e)[:90]}", flush=True)

    # --- Plans grid block, read-only ---
    try:
        pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
        rows=wait_rows(pg)
        print(f"\n  PLANS rows={rows}", flush=True)
        R={}
        def rec(k,s,n): R[k]=(s,str(n)[:430]); print(f"    {k}: {s} — {str(n)[:95]}", flush=True)
        slib.run_grid(pg, rec, "Filter Plans", "Plans", has_crud=False)
        pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
        if wait_rows(pg):
            op=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();return 'ok';}""")
            pg.wait_for_timeout(20000)
            shell=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?d.innerText.slice(0,200).replace(/\\s+/g,' '):'';}""")
            rec("Grid|10","PASS" if shell else "FAIL", f"Re-verified read-only: a plan record opens ({op}). Header: {shell[:120]}")
        n,missed,_=resultio.write("SETTINGS - PLAN ", R)
        print(f"  >> PLAN wrote {n} missed={missed} tally={resultio.tally('SETTINGS - PLAN ')[0]}", flush=True)
    except Exception as e:
        print(f"  PLANS ERR {str(e)[:110]}", flush=True)
    b.close()
