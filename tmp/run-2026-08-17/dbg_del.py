import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
FULL=".md-dialog--full-page"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    errs=[]
    pg.on("console", lambda m: errs.append(m.text[:120]) if m.type=="error" else None)
    pg.on("response", lambda r: errs.append(f"HTTP {r.status} {r.url[-70:]}") if r.status>=400 else None)
    # --- plan removal ---
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Plans")
    print("plan rows before:", pg.evaluate(f"()=>document.querySelectorAll('{FULL} .md-table-row.table-row').length"))
    acts=pg.evaluate(f"""()=>{{const r=document.querySelector('{FULL} .md-table-row.table-row');
      return r?[...r.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim()):[];}}""")
    print("plan row actions:", acts)
    pg.evaluate(f"""()=>{{const r=document.querySelector('{FULL} .md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete|remove/.test(e.textContent));if(a)a.click();}}""")
    pg.wait_for_timeout(3000)
    print("confirm dialog:", (N.sub_text(pg) or '')[:140].replace("\n"," | "))
    errs.clear()
    pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
      const d=ds[ds.length-1];const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}""")
    pg.wait_for_timeout(8000)
    print("after confirm — network/console:", errs[:5])
    print("body toast:", pg.inner_text("body")[:180].replace("\n"," | "))
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
    N.click_tab(pg,"Plans")
    print("plan rows after:", pg.evaluate(f"()=>document.querySelectorAll('{FULL} .md-table-row.table-row').length"))
    b.close()
