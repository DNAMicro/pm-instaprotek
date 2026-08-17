from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
CE="regressiontest_cust_20260817@qamail.test"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    # 1) does my existing Agent test user show in Customers?
    pg.goto(BASE+"/portal/customer", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    s=pg.locator("input[placeholder*='Search']").first
    s.fill("RegressionTest"); pg.wait_for_timeout(4500)
    print("Customers matching 'RegressionTest' (Agent user):", pg.locator(".md-table-row.table-row").count())

    # 2) create a Basic Client user with customer contact details
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)
    def rs(fid,text=None):
        c=pg.locator(f".md-dialog #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
        c.scroll_into_view_if_needed(); c.click(); pg.wait_for_timeout(1300)
        o=(pg.locator(".Select-menu-outer .Select-option",has_text=text).first if text else pg.locator(".Select-menu-outer .Select-option").first)
        o.wait_for(state="visible",timeout=8000); t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(800); return t
    pg.locator(".md-dialog #email").fill(CE)
    pg.locator(".md-dialog #first_name").fill("RegressionTest")
    pg.locator(".md-dialog #last_name").fill("CustomerAug17")
    print("role:", rs("role","Basic Client")); pg.wait_for_timeout(2500)
    for fid,txt in [("user_type",None),("country_lu","United States"),("phone_code","US")]:
        try: print(f"  {fid}:", rs(fid,txt))
        except Exception as e: print(f"  {fid} err:", str(e)[:60])
    try: pg.locator(".md-dialog #mobile_phone").fill("4155550199")
    except Exception as e: print("phone err", str(e)[:50])
    pg.locator(".md-dialog #password").fill("TestPass123!")
    pg.wait_for_timeout(600)
    clicked=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return 'clicked';} return 'disabled';}""")
    pg.wait_for_timeout(6000)
    print("save:", clicked, "| dialogs left:", pg.locator(".md-dialog").count())
    print("body:", pg.inner_text("body")[:200].replace("\n"," | "))

    # 3) does it now appear under Customers?
    pg.goto(BASE+"/portal/customer", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    s=pg.locator("input[placeholder*='Search']").first
    s.fill("regressiontest_cust"); pg.wait_for_timeout(5000)
    n=pg.locator(".md-table-row.table-row").count()
    print("\nCustomers matching new Basic Client:", n)
    if n: print("   row:", pg.locator(".md-table-row.table-row").first.inner_text().replace("\n"," | ")[:200])
    b.close()
