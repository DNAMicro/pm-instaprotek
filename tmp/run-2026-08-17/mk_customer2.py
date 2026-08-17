from playwright.sync_api import sync_playwright
import json
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
CE="regressiontest_cust_20260817@qamail.test"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)
    def rs(fid,text=None):
        c=pg.locator(f".md-dialog #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
        c.scroll_into_view_if_needed(); c.click(); pg.wait_for_timeout(1300)
        o=(pg.locator(".Select-menu-outer .Select-option",has_text=text).first if text else pg.locator(".Select-menu-outer .Select-option").first)
        o.wait_for(state="visible",timeout=8000); t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(800); return t
    def md(tog):
        pg.locator(f".md-dialog #{tog}").click(); pg.wait_for_timeout(1200)
        m=pg.locator(".md-list.md-layover-child")
        m.locator("[role=option]").first.wait_for(state="visible",timeout=8000)
        opts=pg.evaluate("()=>[...document.querySelectorAll('.md-list.md-layover-child [role=option]')].map(e=>e.textContent.trim())")
        t=m.locator("[role=option]").first.inner_text().strip()
        m.locator("[role=option]").first.click(); pg.wait_for_timeout(900)
        return t,opts
    pg.locator(".md-dialog #email").fill(CE)
    pg.locator(".md-dialog #first_name").fill("RegressionTest")
    pg.locator(".md-dialog #last_name").fill("CustomerAug17")
    print("role:", rs("role","Basic Client")); pg.wait_for_timeout(2500)
    t,opts=md("user_type-toggle"); print("user_type:",t," options:",opts)
    print("country:", rs("country_lu","United States"))
    print("code:", rs("phone_code","US"))
    pg.locator(".md-dialog #mobile_phone").fill("4155550199")
    pg.locator(".md-dialog #password").fill("TestPass123!")
    pg.wait_for_timeout(800)
    st=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent));
      return b?{dis:b.disabled}:null;}""")
    print("save btn:", st)
    clicked=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return 'clicked';} return 'disabled';}""")
    pg.wait_for_timeout(7000)
    print("save:",clicked,"| dialogs:",pg.locator(".md-dialog").count())
    body=pg.inner_text("body")
    print("errors:", [m for m in ["is required","Invalid","already exists"] if m in body])
    # verify in users + customers
    for route,label in [("/portal/user","USERS"),("/portal/customer","CUSTOMERS")]:
        pg.goto(BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        s=pg.locator("input[placeholder*='Search']").first; s.fill("regressiontest_cust"); pg.wait_for_timeout(5000)
        n=pg.locator(".md-table-row.table-row").count()
        print(f"{label}: {n} row(s)")
        if n: print("   ", pg.locator(".md-table-row.table-row").first.inner_text().replace("\n"," | ")[:170])
    b.close()
