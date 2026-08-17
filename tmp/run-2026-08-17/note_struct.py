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
    # deepest element containing the note text
    print(pg.evaluate(r"""()=>{
      const all=[...document.querySelectorAll('*')].filter(e=>/RegressionTest Note Aug17/.test(e.textContent));
      const deep=all[all.length-1];
      if(!deep)return 'not found';
      let chain=[]; let e=deep;
      for(let i=0;i<6&&e;i++){chain.push({tag:e.tagName,cls:(e.className||'').toString().slice(0,80),
        btns:[...e.querySelectorAll('button,i.material-icons')].map(x=>x.textContent.trim()).slice(0,10)}); e=e.parentElement;}
      return chain;}"""))
    print("\nPANEL TEXT:")
    print(pg.evaluate(r"""()=>{const ps=[...document.querySelectorAll('.md-tab-panel')].filter(p=>p.offsetParent!==null);
      return ps.map(p=>p.innerText.slice(0,400).replace(/\n/g,' | '));}"""))
    b.close()
