import json
from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
REG="112456244808"
SUB="""(()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('md-dialog--full-page'));
  return ds.length?ds[ds.length-1]:null;})()"""
def open_reg(pg):
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
    pg.locator("input[placeholder*='Search']").first.fill(REG); pg.wait_for_timeout(6000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(6500)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    open_reg(pg)
    print("note present before:", "RegressionTest Note" in pg.inner_text("body"))
    d=pg.evaluate("""()=>{const row=[...document.querySelectorAll('.dataTable__notes__row')].find(r=>/RegressionTest Note/.test(r.innerText));
      if(!row)return 'row-not-found';
      const acts=row.querySelector('.dataTable__notes--actions')||row;
      const b=[...acts.querySelectorAll('button')].find(x=>x.textContent.trim()==='delete');
      if(b){b.click();return 'clicked';}return 'no-delete';}""")
    pg.wait_for_timeout(3500)
    dlg=pg.evaluate(f"()=>{{const d={SUB};return d?d.innerText.replace(/\\n/g,' | '):'';}}")
    print("confirm dialog:", dlg[:140])
    if "delete this note" in dlg.lower():
        c=pg.evaluate(f"""()=>{{const d={SUB};
          const b=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent)&&!/No/.test(x.textContent.replace(/Yes/,'')));
          if(b){{b.click();return b.textContent.trim();}}return 'no-yes';}}""")
        print("clicked:", c)
        pg.wait_for_timeout(7000)
    else:
        print("ABORTED — dialog is not the note-delete confirmation")
    open_reg(pg)
    gone="RegressionTest Note" not in pg.inner_text("body")
    intact=pg.evaluate("""()=>{const t=document.body.innerText;
      return ['Registration Number','Plan','Coverage Amount','Device','Serial Number'].filter(k=>t.includes(k));}""")
    print("NOTE GONE:", gone, "| registration intact:", intact)
    json.dump({"reg":REG,"gone":gone,"intact":intact}, open(EV+"/note_cleanup_final.json","w"), indent=1)
    b.close()
