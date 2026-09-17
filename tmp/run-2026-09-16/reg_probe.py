"""READ-ONLY probe of the New Registration wizard: what fields does it ask for?
Opens the modal and dumps controls. Never saves."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/registration", wait_until="domcontentloaded", timeout=90000)
    for _ in range(50):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    pg.get_by_text("addNew").first.click()
    pg.wait_for_timeout(18000)
    print("dialogs:", pg.locator(".md-dialog").count(), "| fullpage:", pg.locator(".md-dialog--full-page").count())
    txt=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');return d?d.innerText.slice(0,900).replace(/\\s+/g,' '):'(none)';}""")
    print("\nMODAL TEXT:", txt)
    ctrls=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');if(!d)return[];const o=[];
      d.querySelectorAll('input,textarea').forEach(e=>{if(e.type==='hidden')return;
        let l='';if(e.id){const q=d.querySelector('label[for="'+e.id+'"]');if(q)l=q.textContent.trim();}
        if(!l){const w=e.closest('.md-text-field-container,.md-cell,.Select');if(w)l=(w.innerText||'').split('\\n')[0].trim();}
        o.push({id:e.id||null,type:e.type,label:l.slice(0,44),sel:!!e.closest('.Select'),vis:e.offsetParent!==null});});
      d.querySelectorAll('[id$="-toggle"]').forEach(t=>o.push({id:t.id,type:'md-select',
        label:((t.closest('.md-cell,div')||{}).innerText||'').split('\\n')[0].trim().slice(0,44),sel:false,vis:true}));
      return o;}""")
    print("\nCONTROLS:")
    for c in ctrls: print("   ", c)
    btns=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');return d?[...d.querySelectorAll('button')].map(b=>b.innerText.trim().replace(/\\s+/g,' ')).filter(Boolean):[];}""")
    print("\nBUTTONS:", btns)
    pg.screenshot(path=N.EV+"/new_registration_modal.png")
    b.close()
