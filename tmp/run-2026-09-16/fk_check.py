"""READ-ONLY. Open a registration that references the deleted plan and see
whether the plan reference still resolves or is broken."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PLAN="2 - Years Warranty Replacement"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/registration", wait_until="domcontentloaded", timeout=90000)
    for _ in range(40):
        pg.wait_for_timeout(3000)
        if "Filter Registrations" in pg.inner_text("body"): break
    pg.get_by_text("Filter Registrations").first.click(); pg.wait_for_timeout(6000)
    cols=N.rs_open_ph(pg,"Select a filter")
    tgt=next((c for c in cols if "plan" in c.lower()), None)
    N.rs_pick(pg,tgt); pg.wait_for_timeout(5000)
    N.rs_open_ph(pg,"Select a value"); N.rs_pick(pg,PLAN); pg.wait_for_timeout(4000)
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));if(b)b.click();}""")
    pg.wait_for_timeout(22000)
    print("filtered:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'?';}"""), flush=True)
    rows=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].slice(0,5).map(r=>r.innerText.replace(/\\s+/g,' ').trim())""")
    print("\nsample rows referencing the deleted plan:", flush=True)
    for r in rows: print("   ", r[:150], flush=True)
    # open the first one
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(25000)
    print("\nopened registration:", pg.url, flush=True)
    txt=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')||document.querySelector('.advancedFullDialog');
      return d?d.innerText.slice(0,1500):'(no record shell)';}""")
    print(txt.replace("\n"," | ")[:1500], flush=True)
    print("\nplan name still shown on the registration:", PLAN in txt, flush=True)
    print("error indicators:", [k for k in ["No records found","not found","error","null","undefined"] if k.lower() in txt.lower()], flush=True)
    pg.screenshot(path=N.EV+"/fk_registration.png", full_page=False)
    b.close()
