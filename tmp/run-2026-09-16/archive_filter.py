"""READ-ONLY. Build a Status = Archived filter on the Plans grid and look for the deleted plan."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PLAN="2 - Years Warranty Replacement"
def opts(pg): return pg.evaluate("()=>[...document.querySelectorAll('.Select-menu-outer .Select-option')].map(e=>e.textContent.trim())")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
    for _ in range(45):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    print("baseline:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'-';}"""), flush=True)
    pg.get_by_text("Filter Plans").first.click(); pg.wait_for_timeout(6000)

    # open the "Select a filter" control and TYPE to search, rather than reading rendered options
    ctl=pg.locator(".Select", has=pg.locator(".Select-placeholder:has-text('Select a filter')")).first
    ctl.click(); pg.wait_for_timeout(2500)
    print("rendered columns:", opts(pg), flush=True)
    inp=ctl.locator("input").first
    inp.type("stat", delay=90); pg.wait_for_timeout(3000)
    print("after typing 'stat':", opts(pg), flush=True)
    # also scroll the menu to reveal virtualized entries
    pg.evaluate("()=>{const m=document.querySelector('.Select-menu-outer .Select-menu');if(m)m.scrollTop=m.scrollHeight;}")
    pg.wait_for_timeout(1500)
    print("after scroll:", opts(pg), flush=True)

    found=opts(pg)
    target=next((o for o in found if "status" in o.lower()), None)
    print("\nSTATUS COLUMN:", target, flush=True)
    if target:
        pg.locator(".Select-menu-outer .Select-option", has_text=target).first.click(); pg.wait_for_timeout(5000)
        vctl=pg.locator(".Select", has=pg.locator(".Select-placeholder:has-text('Select a value')")).first
        vctl.click(); pg.wait_for_timeout(3500)
        vals=opts(pg); print("STATUS VALUES:", vals, flush=True)
        arch=next((v for v in vals if "archiv" in v.lower()), None)
        print("ARCHIVED VALUE:", arch, flush=True)
        if arch:
            pg.locator(".Select-menu-outer .Select-option", has_text=arch).first.click(); pg.wait_for_timeout(3500)
            pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));if(b)b.click();}""")
            pg.wait_for_timeout(22000)
            pag=pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'-';}""")
            body=pg.inner_text("body")
            print("\n*** ARCHIVED VIEW:", pag, flush=True)
            print("*** DELETED PLAN PRESENT:", PLAN in body, flush=True)
            rows=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].slice(0,15).map(r=>r.innerText.replace(/\\s+/g,' ').trim())""")
            for r in rows: print("   ", r[:150], flush=True)
            pg.screenshot(path=N.EV+"/archived_plans.png", full_page=True)
    else:
        print("no Status column offered in the filter dropdown", flush=True)
    b.close()
