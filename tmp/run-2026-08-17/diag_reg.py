from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    print("rows:", pg.locator(".md-table-row.table-row").count())
    print("has addNew:", pg.get_by_text("addNew").count())
    print("toolbar buttons:", pg.evaluate("()=>[...document.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean).slice(0,18)"))
    # open first record
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    print("\nurl after open:", pg.url)
    print("dialog:", pg.locator(".advancedFullDialog, .md-dialog").count())
    tabs=pg.evaluate("()=>[...document.querySelectorAll('.md-tab-label')].map(e=>e.textContent.trim()).filter(Boolean)")
    print("TABS:", tabs)
    print("\nbody head:", pg.inner_text("body")[:700].replace("\n"," | "))
    pg.screenshot(path=EV+"/reg_record.png")
    b.close()
