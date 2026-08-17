import json, re
from playwright.sync_api import sync_playwright
c = json.load(open('/home/farsheed/pm-instaprotek/credentials.json'))
USER=c['QA']['username']; PW=c['QA']['password']

def probe(base,label,pw):
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        pg=b.new_context(viewport={'width':1600,'height':1000}).new_page()
        try:
            pg.goto(base+"/login",wait_until="domcontentloaded",timeout=60000); pg.wait_for_timeout(2500)
            pg.fill("#email",USER); pg.fill("#password",pw); pg.click("button:has-text('Login')")
            pg.wait_for_timeout(9000)
            if "/portal" not in pg.url:
                print(f"[{label}] LOGIN FAILED: {pg.inner_text('body')[:120]}"); b.close(); return
            t=pg.inner_text("body")
            tot=re.findall(r"Total (Registrations|Claims): ([\d,]+)",t)
            tenant=re.search(r"Logout \| (\w+) \| ([\w ]+)",t.replace("\n"," | "))
            print(f"[{label}] url={pg.url}")
            print(f"    totals={tot}")
            print(f"    tenant/role line={tenant.group(0) if tenant else 'n/a'}")
        except Exception as e: print(f"[{label}] ERR {e}")
        b.close()

probe("https://qa.crm.instaprotek.com","QA",PW)
probe("https://crm.nullnet.instaprotek.com","NULLNET",PW)
