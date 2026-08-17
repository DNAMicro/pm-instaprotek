from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(5000)
    print("url:", pg.url)
    print("dialogs:", pg.locator(".md-dialog").count(), " fullDialog:", pg.locator(".advancedFullDialog").count())
    scope=".md-dialog" if pg.locator(".md-dialog").count() else ".advancedFullDialog"
    print("\n=== FIELDS ===")
    print(pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');if(!d)return 'none';
      return [...d.querySelectorAll('input,textarea')].map(e=>({{id:e.id||null,type:e.type,sel:!!e.closest('.Select'),
        ph:e.placeholder||null,req:/\\*/.test((e.closest('.md-cell,.md-text-field-container')||{{}}).innerText||'')}}));}}"""))
    print("\n=== SELECT PLACEHOLDERS ===")
    print(pg.evaluate(f"""()=>[...document.querySelectorAll('{scope} .Select')].map(s=>s.querySelector('.Select-placeholder')?.textContent.trim()||s.querySelector('.Select-value-label')?.textContent.trim())"""))
    print("\n=== BUTTONS ===")
    print(pg.evaluate(f"""()=>{{const d=document.querySelector('{scope}');return d?[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean):[];}}"""))
    print("\n=== TEXT ===")
    print(pg.inner_text(scope)[:900].replace("\n"," | "))
    pg.screenshot(path=EV+"/reg_new.png")
    b.close()
