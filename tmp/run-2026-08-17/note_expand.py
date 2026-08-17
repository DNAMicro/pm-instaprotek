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
    print("BEFORE expand:", pg.evaluate("""()=>{const li=[...document.querySelectorAll('li.md-expansion-panel')].find(e=>/RegressionTest Note/.test(e.textContent));
      return li?{btns:[...li.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim()),cls:li.className.slice(0,60)}:'no li';}"""))
    # expand via Playwright click (real event) then WAIT
    li=pg.locator("li.md-expansion-panel").filter(has_text="RegressionTest Note").first
    hdr=li.locator(".md-panel-header").first
    hdr.click(); pg.wait_for_timeout(3500)
    print("\nAFTER expand:", pg.evaluate("""()=>{const li=[...document.querySelectorAll('li.md-expansion-panel')].find(e=>/RegressionTest Note/.test(e.textContent));
      return li?{btns:[...li.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim()),
                 expanded:li.className.includes('expanded'), txt:li.innerText.slice(0,200).replace(/\\n/g,' | ')}:'no li';}"""))
    print("\nALL dialogs on page:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog')].map(d=>({
       full:d.classList.contains('advancedFullDialog'), cls:d.className.slice(0,55), txt:d.innerText.slice(0,60).replace(/\\n/g,'|')}))"""))
    pg.screenshot(path=EV+"/note_expanded.png", full_page=True)
    b.close()
