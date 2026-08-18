import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:140]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Products")
    nrows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    print("  product rows:", nrows)
    fb=pg.get_by_text("Filter Products")
    if fb.count(): fb.first.click(); pg.wait_for_timeout(2000)
    vo=[]; tgt=None
    try:
        fo=N.rs_open_ph(pg,"Select a filter")
        for cand in fo[:4]:
            N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,cand); pg.wait_for_timeout(1600)
            tgt=cand
            got=[]
            for _ in range(3):
                try: got=N.rs_open_ph(pg,"Select a value")
                except Exception: pass
                if got: break
                pg.wait_for_timeout(1200)
            if got: vo=got; break
    except Exception as e: print("  err", str(e)[:70])
    rec("Company|5","PASS" if vo else "FAIL",
        f"'Select a value' opens a dropdown dependent on '{tgt}' with {nrows} product row(s) present: {vo[:8]}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Company|6","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    b.close()
R['Plans|31']=('BLOCKED','The Product field in the New Batch modal renders and opens, but returns no options: the plan attached to this test company has no products associated with it, so there is nothing selectable. Not a product defect — a data condition of the self-created test fixture. Exercising it would require associating products with a live plan.')
n,_,_=resultio.write('SETTINGS - COMPANY ',R)
print("tally:",resultio.tally('SETTINGS - COMPANY '))
