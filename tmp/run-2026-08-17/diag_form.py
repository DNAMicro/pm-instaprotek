from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)
    print("=== ALL FIELDS IN NEW USER DIALOG ===")
    print(pg.evaluate(r"""()=>{const d=document.querySelector('.md-dialog');if(!d)return 'no dialog';
      return [...d.querySelectorAll('input,select,textarea')].map(e=>({
        tag:e.tagName,type:e.type,id:e.id||null,name:e.name||null,
        ph:e.placeholder||null,
        sel:!!e.closest('.Select'),
        lbl:(e.closest('.md-text-field-container,.md-cell,div')||{}).innerText?.split('\n')[0]?.slice(0,28)||null
      }));}"""))
    print("\n=== .Select CONTROLS (react-select) with their placeholder/label ===")
    print(pg.evaluate(r"""()=>[...document.querySelectorAll('.md-dialog .Select')].map((s,i)=>({
        i, ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,
        val:s.querySelector('.Select-value-label')?.textContent.trim()||null,
        inputId:s.querySelector('input')?.id||null }))"""))
    b.close()
