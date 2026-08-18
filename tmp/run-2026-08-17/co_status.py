import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    print("status toggle now:", pg.evaluate("""()=>{const t=document.querySelector('.md-dialog--full-page #status-toggle');return t?t.textContent.trim():null;}"""))
    print("status hidden input:", pg.evaluate("""()=>{const e=document.querySelector('.md-dialog--full-page #status');return e?e.value:null;}"""))
    print("company name:", pg.evaluate("""()=>{const e=document.querySelector('.md-dialog--full-page #name');return e?e.value:null;}"""))
    b.close()
