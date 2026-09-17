"""READ-ONLY. Is the Review Questions record-open failure real, or am I clicking the wrong row?"""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1200}).new_page()
    pg.goto(N.BASE+"/portal/review-questions", wait_until="domcontentloaded", timeout=90000)
    for _ in range(50):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    rows=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map((r,i)=>({
      i, text:r.innerText.replace(/\\s+/g,' ').trim().slice(0,90),
      edits:[...r.querySelectorAll('button,i.material-icons')].filter(e=>/edit/.test(e.textContent)).length}))""")
    print(f"rows={len(rows)}")
    for r in rows[:8]: print("  ", r)
    # click the edit belonging to each of the first 3 rows in turn, checking for a modal
    for i in range(min(3,len(rows))):
        pg.goto(N.BASE+"/portal/review-questions", wait_until="domcontentloaded", timeout=90000)
        for _ in range(50):
            pg.wait_for_timeout(3000)
            if pg.locator(".md-table-row.table-row").count()>0: break
        res=pg.evaluate("""(i)=>{const rs=[...document.querySelectorAll('.md-table-row.table-row')];
          const r=rs[i]; if(!r) return 'no-row';
          const e=[...r.querySelectorAll('button,i.material-icons')].filter(x=>/edit/.test(x.textContent));
          if(!e.length) return 'no-edit';
          e[0].scrollIntoView(); e[0].click(); return 'clicked '+e.length+' edit(s) available';}""", i)
        pg.wait_for_timeout(22000)
        info=pg.evaluate("""()=>({dlg:document.querySelectorAll('.md-dialog').length,
          full:document.querySelectorAll('.md-dialog--full-page').length,
          url:location.pathname,
          txt:(document.querySelector('.md-dialog')||{innerText:''}).innerText.slice(0,180).replace(/\\s+/g,' ')})""")
        print(f"  row {i}: {res} -> dlg={info['dlg']} url={info['url']} txt={info['txt'][:110]}")
        pg.screenshot(path=N.EV+f"/reviewq_row{i}.png")
    b.close()
