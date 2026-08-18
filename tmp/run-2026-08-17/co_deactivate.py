import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
FULL=".md-dialog--full-page"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    print("status toggle:", pg.evaluate(f"""()=>{{const t=document.querySelector('{FULL} #status-toggle');return t?t.textContent.trim():null;}}"""))
    try:
        o=N.md_open(pg,"status-toggle")
        print("status options:", o)
        if o:
            N.md_pick(pg,"Inactive")
    except Exception as e: print("status err", str(e)[:70])
    pg.wait_for_timeout(2000)
    sv=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
            ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
    pg.wait_for_timeout(9000)
    pg.goto(N.BASE+"/portal/company", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
    row=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.replace(/\\s+/g,' ').trim()).filter(t=>/RegressionTest/.test(t))""")
    print("save:", sv)
    print("company row now:", row)
    b.close()
