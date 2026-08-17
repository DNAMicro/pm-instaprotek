from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
REG="112456244808"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    s=pg.get_by_placeholder("Search Registrations...")
    if s.count()==0: s=pg.locator("input[placeholder*='Search']").first
    s.fill(REG); pg.wait_for_timeout(6000)
    n=pg.locator(".md-table-row.table-row").count()
    print("rows for", REG, "=", n)
    print("row:", pg.locator(".md-table-row.table-row").first.inner_text().replace("\n"," | ")[:180])
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    print("opened reg:", pg.evaluate("""()=>{const m=document.body.innerText.match(/Registration:\\s*(\\d+)/);return m?m[1]:null;}"""))
    # sanity: is the registration intact?
    print("record intact fields:", pg.evaluate("""()=>{const b=document.body.innerText;
      return ['Registration Number','Plan','Coverage Amount','Device','Serial Number'].filter(k=>b.includes(k));}"""))
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(6000)
    print("\nnote present:", "RegressionTest Note" in pg.inner_text("body"))
    print("\nHOW NOTES RENDER:")
    print(pg.evaluate(r"""()=>{const f=document.querySelector('.advancedFullDialog');
      const hit=[...f.querySelectorAll('*')].filter(e=>/RegressionTest Note/.test(e.textContent)&&e.children.length<4).slice(0,4);
      return hit.map(e=>({tag:e.tagName,cls:(e.className||'').toString().slice(0,70),
        txt:e.innerText.slice(0,80).replace(/\n/g,'|'),
        sibBtns:[...(e.closest('tr,[class*=row],[class*=card],li,div')||e).querySelectorAll('button,i.material-icons')].map(x=>x.textContent.trim()).slice(0,8)}));}"""))
    pg.screenshot(path=EV+"/note_target.png", full_page=True)
    b.close()
