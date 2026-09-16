import sys, os, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
DL="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence/recover"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1400}).new_page()
    pg.goto(N.BASE+"/portal/timeline", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(30000)
    # what Action values exist?
    try:
        pg.get_by_text("Filter Activity").first.click(); pg.wait_for_timeout(5000)
        cols=N.rs_open_ph(pg,"Select a filter"); print("TIMELINE FILTER COLUMNS:", cols, flush=True)
        if "Action" in cols:
            N.rs_pick(pg,"Action"); pg.wait_for_timeout(4000)
            vals=N.rs_open_ph(pg,"Select a value")
            print("ACTION VALUES:", vals, flush=True)
            plan_actions=[v for v in vals if "plan" in v.lower()]
            print("PLAN-RELATED ACTIONS:", plan_actions, flush=True)
            target=next((v for v in vals if "delete" in v.lower() and "plan" in v.lower()), None)
            if target:
                N.rs_pick(pg, target); pg.wait_for_timeout(3000)
                pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));if(b)b.click();}""")
                pg.wait_for_timeout(15000)
                t=pg.inner_text("body")
                print(f"\n=== TIMELINE FILTERED TO '{target}' ===", flush=True)
                print(t[:3000].replace("\n"," | "), flush=True)
                pg.screenshot(path=DL+"/timeline_delete_plan.png", full_page=True)
            else:
                print("\nNo 'Delete Plan' action value exists in the timeline.", flush=True)
    except Exception as e:
        print("timeline filter ERR:", str(e)[:150], flush=True)
    # raw scan of today's entries mentioning the plan name
    body=pg.inner_text("body")
    for kw in ["Years Warranty Replacement","Delete Plan","Delete"]:
        hits=[l.strip() for l in body.split("\n") if kw.lower() in l.lower()]
        print(f"\nRAW '{kw}': {len(hits)} line(s)", flush=True)
        for h in hits[:10]: print("   ", h[:160], flush=True)
    b.close()
