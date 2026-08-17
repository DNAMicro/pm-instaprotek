from playwright.sync_api import sync_playwright
import json
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
CE="regressiontest_cust_20260817@qamail.test"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)
    def rs(fid,text=None):
        c=pg.locator(f".md-dialog #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
        c.scroll_into_view_if_needed(); c.click(); pg.wait_for_timeout(1400)
        o=(pg.locator(".Select-menu-outer .Select-option",has_text=text).first if text else pg.locator(".Select-menu-outer .Select-option").first)
        o.wait_for(state="visible",timeout=9000); t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(900); return t
    pg.locator(".md-dialog #email").fill(CE)
    pg.locator(".md-dialog #first_name").fill("RegressionTest")
    pg.locator(".md-dialog #last_name").fill("CustomerAug17")
    rs("role","Basic Client"); pg.wait_for_timeout(2500)
    pg.locator(".md-dialog #user_type-toggle").click(); pg.wait_for_timeout(1200)
    pg.locator(".md-list.md-layover-child [role=option]", has_text="End User").last.click(); pg.wait_for_timeout(1500)
    rs("country_lu","United States"); rs("phone_code","US")
    pg.locator(".md-dialog #mobile_phone").fill("4155550199")
    rs("language","English"); rs("company")
    pg.locator(".md-dialog #password").fill("TestPass123!")
    pg.wait_for_timeout(800)

    # ---- ADDRESS (custom autocomplete) ----
    ai=pg.get_by_placeholder("Search address")
    print("address input present:", ai.count())
    if ai.count():
        ai.first.scroll_into_view_if_needed(); ai.first.click(); ai.first.fill("")
        ai.first.type("1600 Amphitheatre Parkway, Mountain View", delay=90)
        try:
            it=pg.locator(".address__suggestion__item").first
            it.wait_for(state="visible", timeout=10000); pg.wait_for_timeout(400)
            print("suggestion:", it.inner_text()[:60]); it.click(); pg.wait_for_timeout(1500)
        except Exception as e: print("suggest err:", str(e)[:70])
        for fid,val in [("street","1600 Amphitheatre Parkway"),("city","Mountain View"),("zip_code","94043")]:
            L=pg.locator(f".md-dialog #{fid}")
            if L.count() and not L.first.input_value(): L.first.fill(val)
        for fid,txt in [("country","United States"),("state","California")]:
            try:
                if pg.locator(f".md-dialog #{fid}").count(): print(f"  {fid}:", rs(fid,txt))
            except Exception as e: print(f"  {fid} err:", str(e)[:50])
    pg.wait_for_timeout(1000)
    clicked=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return 'clicked';} return 'disabled';}""")
    pg.wait_for_timeout(9000)
    print("save:",clicked," dialogs:",pg.locator(".md-dialog").count())
    print("errs:", pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,6);}"""))
    pg.screenshot(path=EV+"/cust_create.png", full_page=True)
    for route,label in [("/portal/user","USERS"),("/portal/customer","CUSTOMERS")]:
        pg.goto(BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        s=pg.locator("input[placeholder*='Search']").first; s.fill("regressiontest_cust"); pg.wait_for_timeout(5500)
        n=pg.locator(".md-table-row.table-row").count()
        print(f"{label}: {n} row(s)")
        if n: print("   ", pg.locator(".md-table-row.table-row").first.inner_text().replace("\n"," | ")[:180])
    b.close()
