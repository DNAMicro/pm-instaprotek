import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for route,label in [("/portal/affiliate","Affiliate"),("/portal/company","Company")]:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        n=N.search_grid(pg,"RegressionTest")
        print(f"\n=== {label}: {n} row(s) ===")
        if n<=0: continue
        info=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          return [...r.querySelectorAll('button')].map((b,i)=>({i,txt:b.textContent.trim(),cls:b.className.slice(0,40)}));}""")
        print(" row buttons:", info)
        r=pg.evaluate("""()=>{const row=document.querySelector('.md-table-row.table-row');
          const btns=[...row.querySelectorAll('button')];
          const del=btns.find(b=>/delete/i.test(b.textContent));
          if(!del)return 'no-delete-button';
          del.scrollIntoView({block:'center'});
          del.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
          return 'dispatched';}""")
        pg.wait_for_timeout(5000)
        print(" click:", r, "| dialogs:", pg.locator(".md-dialog").count())
        txt=N.sub_text(pg) or ""
        print(" dialog text:", txt[:120].replace("\n"," | "))
        if "sure" in txt.lower() or "delete" in txt.lower():
            c=pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
              const d=ds[ds.length-1];const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));
              if(y){y.click();return 'yes';}return 'no-yes';}""")
            pg.wait_for_timeout(8000)
            print(" confirmed:", c)
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        print(" remaining:", N.search_grid(pg,"RegressionTest"))
    b.close()
