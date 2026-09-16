"""READ-ONLY. How many registrations reference the deleted plan?
Uses the grid FILTER (not the search box, which does not filter)."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PLAN="2 - Years Warranty Replacement"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050}).new_page()
    pg.goto(N.BASE+"/portal/registration", wait_until="domcontentloaded", timeout=90000)
    for _ in range(40):
        pg.wait_for_timeout(3000)
        if "Filter Registrations" in pg.inner_text("body"): break
    print("total registrations:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'?';}"""), flush=True)
    try:
        pg.get_by_text("Filter Registrations").first.click(); pg.wait_for_timeout(6000)
        cols=N.rs_open_ph(pg,"Select a filter")
        print("filter columns:", cols, flush=True)
        tgt=next((c for c in cols if "plan" in c.lower()), None)
        print("plan column:", tgt, flush=True)
        if tgt:
            N.rs_pick(pg,tgt); pg.wait_for_timeout(5000)
            vals=N.rs_open_ph(pg,"Select a value")
            print(f"plan values available ({len(vals)}):", flush=True)
            for v in vals: print("   -", v, flush=True)
            print(f"\n*** '{PLAN}' still offered as a filter value: {PLAN in vals} ***", flush=True)
            if PLAN in vals:
                N.rs_pick(pg,PLAN); pg.wait_for_timeout(4000)
                pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));if(b)b.click();}""")
                pg.wait_for_timeout(20000)
                print("FILTERED COUNT:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'0 / none';}"""), flush=True)
                pg.screenshot(path=N.EV+"/blast_radius.png", full_page=False)
    except Exception as e:
        print("filter probe failed:", str(e)[:140], flush=True)
    b.close()
