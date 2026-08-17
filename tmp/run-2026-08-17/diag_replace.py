from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    print("=== DETAILS TAB: file inputs & replace-ish controls ===")
    print("file inputs:", pg.evaluate("()=>[...document.querySelectorAll('input[type=file]')].map(e=>({id:e.id,vis:e.offsetParent!==null}))"))
    print("controls matching replace/upload/change:", pg.evaluate(r"""()=>[...document.querySelectorAll('button,i.material-icons,label,a')]
      .filter(e=>/replace|upload|change|attach/i.test(e.textContent)).map(e=>({t:e.textContent.trim().slice(0,26),vis:e.offsetParent!==null}))"""))
    print("\nreceipt section text:", pg.evaluate(r"""()=>{const t=document.body.innerText;
      const i=t.indexOf('Store Receipt'); return i<0?'(no Store Receipt heading)':t.slice(i,i+320).replace(/\n/g,' | ');}"""))
    # open View Receipt and re-inspect
    vr=pg.get_by_text("View Receipt")
    if vr.count():
        vr.first.click(); pg.wait_for_timeout(6000)
        print("\n=== AFTER View Receipt ===")
        print("dialogs:", pg.evaluate("()=>[...document.querySelectorAll('.md-dialog')].map(d=>({full:d.classList.contains('md-dialog--full-page'),txt:d.innerText.slice(0,70).replace(/\\n/g,'|')}))"))
        print("file inputs now:", pg.evaluate("()=>[...document.querySelectorAll('input[type=file]')].map(e=>({id:e.id,vis:e.offsetParent!==null}))"))
        print("replace controls now:", pg.evaluate(r"""()=>[...document.querySelectorAll('button,label,a,i')]
          .filter(e=>/replace|upload|change/i.test(e.textContent)).map(e=>e.textContent.trim().slice(0,26))"""))
    b.close()
