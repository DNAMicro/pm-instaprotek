from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)
    c=pg.locator(".md-dialog #role").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
    c.click(); pg.wait_for_timeout(1200)
    pg.locator(".Select-menu-outer .Select-option",has_text="Basic Client").first.click(); pg.wait_for_timeout(3000)
    print(pg.evaluate(r"""()=>{const d=document.querySelector('.md-dialog');
      const e=d.querySelector('#user_type');
      if(!e)return 'no #user_type';
      return {tag:e.tagName,type:e.type,cls:e.className,vis:e.offsetParent!==null,
              inSelect:!!e.closest('.Select'),
              parentCls:e.parentElement.className,
              gp:e.parentElement.parentElement.className,
              outer:e.outerHTML.slice(0,240)};}"""))
    print("\ntoggles present:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog [id$=-toggle]')].map(e=>e.id)"""))
    print("\nall .Select input ids:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog .Select input')].map(e=>e.id)"""))
    b.close()
