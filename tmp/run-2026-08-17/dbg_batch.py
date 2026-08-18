import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Plans")
    n=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    print("company plan rows:", n)
    print("row:", pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');return r?r.innerText.replace(/\\s+/g,' ').slice(0,120):null;}"""))
    pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    N.click_tab(pg,"Batches"); N.add_new_in_record(pg)
    print("\nNEW BATCH text:", N.sub_text(pg)[:300].replace("\n"," | "))
    print("controls:", [(c['id'],c['label'],c['type'],c['isSelect']) for c in S.controls(pg)])
    print("selects:", pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('.Select')].map(s=>({{
      id:(s.querySelector('input')||{{}}).id||null,
      ph:(s.querySelector('.Select-placeholder')||{{}}).textContent||null}}));}}"""))
    b.close()
