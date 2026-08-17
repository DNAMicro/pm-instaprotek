from playwright.sync_api import sync_playwright
D="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence/"
BASE="https://crm.nullnet.instaprotek.com"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=D+"auth_state.json",viewport={'width':1500,'height':900}).new_page()
    pg.goto(BASE+"/portal/dashboard",wait_until="domcontentloaded",timeout=60000)
    pg.wait_for_timeout(6000)
    print("BASE URL CONFIGURED :", BASE)
    print("BROWSER IS ON       :", pg.url)
    print("PAGE TITLE          :", pg.title())
    print("LOGGED-IN AS        :", pg.inner_text("body").split("Logout")[1][:40].replace("\n"," | ").strip())
    print("AUTHENTICATED       :", "/portal" in pg.url)
    b.close()
