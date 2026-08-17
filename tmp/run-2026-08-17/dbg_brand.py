import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/brand", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    n=N.search_grid(pg,"RegressionTest")
    print("leftover brand rows:", n)
    if n:
        print("row:", pg.locator(".md-table-row.table-row").first.inner_text().replace("\n"," | ")[:120])
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
        pg.wait_for_timeout(8000)
        print("record buttons:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog--full-page button')].map(b=>b.textContent.trim()).filter(Boolean).slice(0,16)"""))
        N.click_tab(pg,"Devices")
        print("device rows under brand:", pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length"""))
        print("device row text:", pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');return r?r.innerText.replace(/\\s+/g,' ').slice(0,90):null;}"""))
        # inspect New Device modal controls for id-type/workflow
        N.add_new_in_record(pg)
        print("\nNEW DEVICE controls:", pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
          return {{radios:d.querySelectorAll('input[type=radio]').length,
                   checks:d.querySelectorAll('input[type=checkbox]').length,
                   selcontrols:[...d.querySelectorAll('.md-selection-control-container')].map(e=>e.innerText.trim().slice(0,30)).slice(0,10),
                   text:d.innerText.slice(0,400).replace(/\\n/g,' | ')}};}}"""))
        N.sub_click(pg,"Cancel")
    b.close()
