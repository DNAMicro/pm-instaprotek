import json
from playwright.sync_api import sync_playwright
c = json.load(open('/home/farsheed/pm-instaprotek/credentials.json'))
USER = c['QA']['username']; PW = c['QA']['password']

def attempt(base, user, pw, label):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(viewport={'width':1400,'height':900}).new_page()
        try:
            pg.goto(base + "/login", wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(2500)
            pg.fill("#email", user); pg.fill("#password", pw)
            pg.click("button:has-text('Login')")
            pg.wait_for_timeout(7000)
            txt = pg.inner_text("body").replace("\n"," | ")
            msg = [s for s in ["Incorrect password","not found","does not exist","Invalid","invalid","inactive","Unauthorized","error"] if s in txt]
            print(f"[{label}] url={pg.url}  markers={msg}")
            print(f"    body={txt[:260]}")
        except Exception as e:
            print(f"[{label}] EXCEPTION {e}")
        b.close()

attempt("https://qa.crm.instaprotek.com", USER, PW, "QA / real creds")
attempt("https://crm.nullnet.instaprotek.com", USER, PW, "NULLNET / real creds")
attempt("https://crm.nullnet.instaprotek.com", "nosuchuser_zz@dnamicro.com", "whatever123", "NULLNET / bogus user")
