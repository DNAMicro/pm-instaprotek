import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
FULL=".md-dialog--full-page"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    net=[]
    pg.on("response", lambda r: net.append(f"{r.request.method} {r.status} {r.url[-60:]}") if (r.status>=400 or '/company' in r.url) else None)
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    net.clear()
    d=pg.evaluate(f"""()=>{{const dl=document.querySelector('{FULL}');
      const b=[...dl.querySelectorAll('button')].find(x=>/Delete/i.test(x.textContent));
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
    pg.wait_for_timeout(3000)
    print("delete click:", d, "| dialog:", (N.sub_text(pg) or '')[:110].replace("\n"," | "))
    net.clear()
    pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
      const dd=ds[ds.length-1];const y=[...dd.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}""")
    pg.wait_for_timeout(9000)
    print("network after confirm:", [x for x in net if 'DELETE' in x or ' 4' in x or ' 5' in x][:6])
    print("all company calls:", net[:8])
    pg.goto(N.BASE+"/portal/company", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    hits=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.replace(/\\s+/g,' ').trim()).filter(t=>/RegressionTest/.test(t))""")
    print("company still present:", hits)
    b.close()
