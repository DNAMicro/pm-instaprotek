from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/users", wait_until="domcontentloaded", timeout=60000)
    for t in (5,10,20,30):
        pg.wait_for_timeout(5000 if t==5 else 5000 if t==10 else 10000)
        rows=pg.locator(".md-table-row").count()
        print(f"  t~{t}s url={pg.url} rows={rows} preloader={'Getting Records' in pg.inner_text('body')}")
        if rows: break
    print("--- BODY ---")
    print(pg.inner_text("body")[:1200].replace("\n"," | "))
    print("--- BUTTONS ---")
    print(pg.evaluate("()=>[...document.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean).slice(0,25)"))
    pg.screenshot(path=EV+"/users_diag.png", full_page=False)
    b.close()
