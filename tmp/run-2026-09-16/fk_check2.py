"""READ-ONLY. Read the actual input VALUES on a registration that referenced the deleted plan."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
URL="https://crm.instaprotek.com/portal/registration/9d5efa0f-c54f-4237-b044-492767daa709"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(30000)
    data=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')||document.querySelector('.advancedFullDialog')||document;
      const out=[];
      d.querySelectorAll('input,textarea').forEach(e=>{
        if(e.type==='hidden')return;
        let lbl='';
        if(e.id){const l=d.querySelector('label[for="'+e.id+'"]');if(l)lbl=l.textContent.trim();}
        if(!lbl){const w=e.closest('.md-text-field-container,.md-cell,.Select');if(w)lbl=(w.innerText||'').split('\\n')[0].trim();}
        out.push({label:lbl.slice(0,40), id:(e.id||'').slice(0,30), value:(e.value||'').slice(0,60)});});
      // react-select rendered values
      d.querySelectorAll('.Select').forEach(s=>{
        const v=s.querySelector('.Select-value-label'); const ph=s.querySelector('.Select-placeholder');
        out.push({label:'[Select] '+((s.closest('.md-cell')||s).innerText||'').split('\\n')[0].trim().slice(0,34),
                  id:'', value: v?v.textContent.trim():(ph?'(placeholder: '+ph.textContent.trim()+')':'(EMPTY)')});});
      return out;}""")
    print("=== INPUT / SELECT VALUES ON REGISTRATION 680399676351 ===", flush=True)
    for d in data:
        if d['label'] or d['value']:
            print(f"  {d['label'][:38]:40s} | {d['value'][:58]}", flush=True)
    plan=[d for d in data if 'plan' in (d['label']+d['id']).lower()]
    print("\n=== PLAN-RELATED FIELDS ===", flush=True)
    for d in plan: print("   ", d, flush=True)
    pg.screenshot(path=N.EV+"/fk_registration_values.png", full_page=False)
    b.close()
