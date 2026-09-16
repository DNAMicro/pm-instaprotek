import json, sys
from playwright.sync_api import sync_playwright
C=json.load(open("/home/farsheed/pm-instaprotek/credentials.json"))["Production"]
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={"width":1600,"height":1000}, accept_downloads=True)
    pg=ctx.new_page()
    pg.goto(C["crm_base_url"], wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(4000)
    print("URL0:", pg.url)
    print("TITLE:", pg.title())
    # find inputs
    ins=pg.evaluate("()=>[...document.querySelectorAll('input')].map(i=>({t:i.type,n:i.name,id:i.id,ph:i.placeholder}))")
    print("INPUTS:", ins)
    try:
        pg.fill("#email", C["username"])
        pg.fill("#password", C["password"])
        pg.wait_for_timeout(500)
        btns=pg.evaluate("()=>[...document.querySelectorAll('button')].map(b=>b.textContent.trim())")
        print("BTNS:", btns)
        pg.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(x=>/log ?in|sign ?in|submit/i.test(x.textContent));if(b)b.click();}")
        pg.wait_for_timeout(9000)
    except Exception as e:
        print("LOGIN-ERR:", e)
    print("URL1:", pg.url)
    print("BODY:", pg.inner_text("body")[:900])
    ctx.storage_state(path=EV+"/auth_state.json")
    pg.screenshot(path=EV+"/login.png", full_page=False)
    b.close()
