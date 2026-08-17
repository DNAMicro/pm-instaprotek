from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    print("reg:", pg.evaluate("""()=>{const m=document.body.innerText.match(/Registration:\\s*(\\d+)/);return m?m[1]:null;}"""))
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(7000)
    print("note present in body:", "RegressionTest Note" in pg.inner_text("body"))
    print("\nrow classes inside full dialog:", pg.evaluate("""()=>{const f=document.querySelector('.advancedFullDialog');
      const rows=[...f.querySelectorAll('tr,[class*=table-row],[class*=row]')].slice(0,12);
      return rows.map(r=>({cls:r.className.slice(0,60), txt:r.innerText.slice(0,60).replace(/\\n/g,'|')}));}"""))
    print("\nnotes panel text:", pg.evaluate("""()=>{const p=document.querySelector('.md-tab-panel.fullpageDialog__tabsPanel');
      return p?p.innerText.slice(0,500).replace(/\\n/g,' | '):'no panel';}"""))
    b.close()
