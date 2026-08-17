import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/repair-network", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    rows=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.replace(/\\s+/g,' ').trim())""")
    print("repair network rows:", rows)
    R={
      'Grid|5':('FAIL', f"'Select a value' returns no options. The only filter column offered is 'Repair Network Name' and selecting it yields an empty value dropdown even though the grid holds {len(rows)} record(s): {rows}. No JavaScript error is raised and the page stays usable. Expected: the value list is populated from the selected column."),
      'Grid|6':('BLOCKED', "No value could be selected because the dependent value dropdown returns no options (see Grid|5)."),
    }
    n,_,_=resultio.write('SETTINGS - REPAIR NETWORk ',R,defects={'Grid|5':'DEF-SET-02'})
    print('updated',n,'tally',resultio.tally('SETTINGS - REPAIR NETWORk '))
    b.close()
