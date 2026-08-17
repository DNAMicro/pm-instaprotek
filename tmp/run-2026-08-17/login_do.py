import json
from playwright.sync_api import sync_playwright
BASE = "https://crm.nullnet.instaprotek.com"
c = json.load(open('/home/farsheed/pm-instaprotek/credentials.json'))
USER = c['QA']['username']; PW = c['QA']['password']
D="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence/"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width':1600,'height':1000})
    pg = ctx.new_page()
    pg.goto(BASE + "/login", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(2500)
    pg.fill("#email", USER); pg.fill("#password", PW)
    pg.click("button:has-text('Login')")
    pg.wait_for_timeout(8000)
    print("URL after login:", pg.url)
    print("BODY:", pg.inner_text("body")[:900].replace("\n"," | "))
    pg.screenshot(path=D+"after_login.png", full_page=True)
    if "/portal" in pg.url:
        ctx.storage_state(path=D+"auth_state.json")
        print(">>> LOGIN OK, auth state saved")
    else:
        print(">>> LOGIN DID NOT REACH PORTAL")
    b.close()
