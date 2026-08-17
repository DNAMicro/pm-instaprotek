from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
def fields(pg):
    return pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');if(!d)return[];
      return [...d.querySelectorAll('input')].map(e=>e.id||e.type);}""")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)
    print("baseline fields:", fields(pg))
    ctrl=pg.locator(".md-dialog #role").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
    ctrl.click(); pg.wait_for_timeout(1200)
    roles=pg.evaluate("()=>[...document.querySelectorAll('.Select-menu-outer .Select-option')].map(e=>e.textContent.trim())")
    print("roles available:", roles)
    for role in roles:
        try:
            ctrl.click(); pg.wait_for_timeout(900)
            pg.locator(".Select-menu-outer .Select-option", has_text=role).first.click()
            pg.wait_for_timeout(2000)
            f=fields(pg)
            extra=[x for x in f if any(k in str(x).lower() for k in ('country','phone','address','state','zip'))]
            print(f"  role={role:16s} fields={f}  contact-fields={extra or 'NONE'}")
        except Exception as e:
            print(f"  role={role:16s} ERR {str(e)[:60]}")
    b.close()
