from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/customer", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    print("rows:", pg.locator(".md-table-row.table-row").count())
    print("addNew present:", pg.get_by_text("addNew").count())
    print("buttons:", pg.evaluate("()=>[...document.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean).slice(0,14)"))
    if pg.get_by_text("addNew").count():
        pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4500)
        sc=".md-dialog" if pg.locator(".md-dialog").count() else ".advancedFullDialog"
        print("\n=== NEW CUSTOMER FORM ===")
        print("fields:", pg.evaluate(f"""()=>{{const d=document.querySelector('{sc}');if(!d)return[];
          return [...d.querySelectorAll('input,textarea')].map(e=>({{id:e.id||null,type:e.type,vis:e.offsetParent!==null,sel:!!e.closest('.Select')}}));}}"""))
        print("selects:", pg.evaluate(f"""()=>[...document.querySelectorAll('{sc} .Select')].map(s=>s.querySelector('.Select-placeholder')?.textContent.trim())"""))
        print("buttons:", pg.evaluate(f"""()=>{{const d=document.querySelector('{sc}');return d?[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean):[];}}"""))
        print("text:", pg.inner_text(sc)[:400].replace("\n"," | "))
    b.close()
