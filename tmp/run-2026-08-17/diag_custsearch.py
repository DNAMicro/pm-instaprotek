from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(5000)
    sf=pg.get_by_placeholder("Search Customer...")
    for term in ["regressiontest_cust","RegressionTest","CustomerAug17"]:
        sf.fill(""); sf.fill(term); pg.wait_for_timeout(5000)
        rows=pg.locator(".md-dialog .md-table-row.table-row").count()
        print(f"customer search '{term}' -> {rows} rows")
        if rows:
            print("   ", pg.locator(".md-dialog .md-table-row.table-row").first.inner_text().replace("\n"," | ")[:150])
            break
    b.close()
