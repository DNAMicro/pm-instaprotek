from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    s=pg.locator("input[placeholder*='Search']").first
    for term in ["RegressionTest","UserAug17","regressiontest_20260817"]:
        s.fill(""); s.fill(term); pg.wait_for_timeout(4000)
        n=pg.locator(".md-table-row.table-row").count()
        print(f"search '{term}' -> {n} rows")
        if n:
            print("   row:", pg.locator(".md-table-row.table-row").first.inner_text().replace("\n"," | ")[:200])
            break
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent)); (a||r).click();}""")
    pg.wait_for_timeout(5000)
    print("\n=== RECORD DIALOG FIELDS ===")
    print(pg.evaluate(r"""()=>{const d=document.querySelector('.advancedFullDialog')||document.querySelector('.md-dialog');
      if(!d)return 'none';
      return [...d.querySelectorAll('input,textarea')].map(e=>({id:e.id||null,type:e.type,val:(e.value||'').slice(0,34),disabled:e.disabled,ro:e.readOnly,sel:!!e.closest('.Select')}));}"""))
    print("\n=== BUTTONS IN RECORD ===")
    print(pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog')||document.querySelector('.md-dialog');
      return d?[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean):[];}"""))
    # open change password
    cp=pg.get_by_text("Change Password")
    if cp.count():
        cp.first.click(); pg.wait_for_timeout(3000)
        print("\n=== AFTER Change Password CLICK ===")
        print("dialogs:", pg.locator(".md-dialog").count())
        print(pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog')].map(d=>({
           inputs:[...d.querySelectorAll('input')].map(i=>({id:i.id,type:i.type})),
           btns:[...d.querySelectorAll('button')].map(b=>({t:b.textContent.trim(),dis:b.disabled}))}))"""))
    pg.screenshot(path=EV+"/users/record_diag.png")
    b.close()
