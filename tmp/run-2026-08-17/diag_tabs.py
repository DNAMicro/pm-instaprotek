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
    print("containers:", pg.evaluate("""()=>({full:document.querySelectorAll('.advancedFullDialog').length,
       dlg:document.querySelectorAll('.md-dialog').length,
       fullIsDlg:[...document.querySelectorAll('.advancedFullDialog')].map(e=>e.className.includes('md-dialog'))})"""))
    for tab in ["Notes","Claim"]:
        pg.evaluate(f"""()=>{{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='{tab}');if(t)t.click();}}""")
        pg.wait_for_timeout(6000)
        print(f"\n=== {tab} TAB ===")
        print(" addNew elements & their container:", pg.evaluate("""()=>[...document.querySelectorAll('button,i')].filter(e=>/addNew/.test(e.textContent)).map(e=>({
            txt:e.textContent.trim().slice(0,12),
            inFull:!!e.closest('.advancedFullDialog'),
            vis:e.offsetParent!==null,
            path:(e.closest('[class*=tab-panel],[class*=md-tab]')||{}).className?.slice(0,40)||null}))"""))
        print(" panel text:", pg.evaluate("""()=>{const f=document.querySelector('.advancedFullDialog');
            return f?f.innerText.slice(0,300).replace(/\\n/g,' | '):'no full dialog';}"""))
    # click the visible addNew inside the full dialog on Notes
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(6000)
    r=pg.evaluate("""()=>{const els=[...document.querySelectorAll('.advancedFullDialog button,.advancedFullDialog i')].filter(e=>/addNew/.test(e.textContent)&&e.offsetParent!==null);
       if(els.length){els[0].click();return els.length;}return 0;}""")
    pg.wait_for_timeout(6000)
    print("\nafter scoped addNew click (n=%s):"%r)
    print(" dialogs:", pg.locator(".md-dialog").count())
    print(" newest dialog text:", pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];
       const d=ds[ds.length-1];return d?d.innerText.slice(0,300).replace(/\\n/g,' | '):'none';}"""))
    print(" newest dialog inputs:", pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];const d=ds[ds.length-1];
       return d?[...d.querySelectorAll('input,textarea,[contenteditable=true]')].map(e=>e.id||e.tagName+':'+(e.getAttribute('contenteditable')||e.type)):[];}"""))
    b.close()
