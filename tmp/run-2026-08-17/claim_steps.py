from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
SUB="""(()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('md-dialog--full-page'));
  return ds.length?ds[ds.length-1]:null;})()"""
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Claim');if(t)t.click();}""")
    pg.wait_for_timeout(6500)
    pg.evaluate("""()=>{const els=[...document.querySelectorAll('.md-dialog--full-page button,.md-dialog--full-page i')]
       .filter(e=>/addNew/.test(e.textContent)&&e.offsetParent!==null); if(els.length)els[0].click();}""")
    pg.wait_for_timeout(7000)
    for step in range(1,5):
        info=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return null;
          return {{head:d.innerText.slice(0,120).replace(/\\n/g,' | '),
                   steps:[...d.querySelectorAll('.md-stepper,[class*=step]')].length,
                   textareas:[...d.querySelectorAll('textarea')].map(t=>({{id:t.id,vis:t.offsetParent!==null}})),
                   editables:[...d.querySelectorAll('[contenteditable=true]')].map(t=>({{vis:t.offsetParent!==null}})),
                   notesWord:/notes?/i.test(d.innerText),
                   btns:[...d.querySelectorAll('button')].map(x=>x.textContent.trim()).slice(-5)}};}}""")
        print(f"\n--- wizard state {step} ---")
        print(" head:", info["head"] if info else None)
        print(" textareas:", info["textareas"] if info else None, " editables:", info["editables"] if info else None)
        print(" mentions 'note':", info["notesWord"] if info else None)
        print(" buttons:", info["btns"] if info else None)
        r=pg.evaluate(f"""()=>{{const d={SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);
          if(b){{b.click();return 'next';}}return 'no-next';}}""")
        if r=='no-next': print(" >> no Next available; wizard ends here"); break
        pg.wait_for_timeout(6000)
    # cancel
    pg.evaluate(f"""()=>{{const d={SUB};const c=[...d.querySelectorAll('button')].find(x=>/Cancel/i.test(x.textContent));if(c)c.click();}}""")
    print("\ncancelled")
    b.close()
