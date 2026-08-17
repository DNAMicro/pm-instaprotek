import json, sys
from playwright.sync_api import sync_playwright

BASE = "https://crm.nullnet.instaprotek.com"
c = json.load(open('/home/farsheed/pm-instaprotek/credentials.json'))
USER = c['QA']['username']; PW = c['QA']['password']

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width':1600,'height':1000})
    pg.goto(BASE + "/login", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(3000)
    print("URL after load:", pg.url)
    print("TITLE:", pg.title())
    # dump visible inputs
    for sel in ["input"]:
        for el in pg.locator(sel).all():
            try:
                print("  input:", el.get_attribute("type"), el.get_attribute("name"), el.get_attribute("id"), "visible=", el.is_visible())
            except Exception as e: pass
    print("BODY SNIPPET:", pg.inner_text("body")[:600].replace("\n"," | "))
    pg.screenshot(path="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence/login_page.png", full_page=True)
    b.close()
