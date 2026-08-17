from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
REG="112456244808"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.locator("input[placeholder*='Search']").first.fill(REG); pg.wait_for_timeout(6000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(6500)
    print("notes-area buttons (visible), with their container chain:")
    print(pg.evaluate(r"""()=>{
      const cont=document.querySelector('.dataTable__notes--content')||document.querySelector('.md-tab-panel:not([aria-hidden=true])');
      const root=cont?cont.closest('.md-tab-panel')||cont:document.body;
      return [...root.querySelectorAll('button,i.material-icons')]
        .filter(e=>e.offsetParent!==null)
        .map(e=>({txt:e.textContent.trim().slice(0,18),
                  cls:(e.className||'').toString().slice(0,45),
                  parent:(e.parentElement.className||'').toString().slice(0,45)}));}"""))
    print("\ndataTable__notes structure:")
    print(pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=dataTable__notes]')].map(e=>({
      cls:e.className.slice(0,60), txt:e.innerText.slice(0,90).replace(/\n/g,'|'),
      btns:[...e.querySelectorAll('button,i.material-icons')].map(x=>x.textContent.trim()).slice(0,6)}))"""))
    b.close()
