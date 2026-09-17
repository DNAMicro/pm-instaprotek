import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    # 1. is the Registration Survey grid genuinely empty?
    pg.goto(N.BASE+"/portal/survey", wait_until="domcontentloaded", timeout=90000); pg.wait_for_timeout(35000)
    t=pg.inner_text("body")
    print("=== /portal/survey ===")
    print("  rows:", pg.locator(".md-table-row.table-row").count())
    print("  pagination:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'-';}"""))
    print("  'no records' shown:", "No records found" in t or "no record" in t.lower())
    print("  New button present:", pg.get_by_text("addNew").count())
    print("  body:", t[:420].replace("\n"," | "))
    # 2. can a registration be created from the portal at all?
    pg.goto(N.BASE+"/portal/registration", wait_until="domcontentloaded", timeout=90000)
    for _ in range(50):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    print("\n=== /portal/registration ===")
    print("  rows:", pg.locator(".md-table-row.table-row").count())
    print("  pagination:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of [\\d,]+/);return m?m[0]:'-';}"""))
    btns=pg.evaluate("()=>[...new Set([...document.querySelectorAll('button')].map(b=>b.innerText.trim().replace(/\\s+/g,' ')))].filter(Boolean)")
    print("  buttons:", btns[:14])
    print("  New/addNew present:", pg.get_by_text("addNew").count())
    b.close()
