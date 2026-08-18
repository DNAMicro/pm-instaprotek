import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
AFF=json.load(open(N.EV+"/aff_ctx.json"))["aff_url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    # 1) delete the store under the affiliate
    pg.goto(AFF, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Stores")
    for i in range(4):
        n=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
        print(f"  store rows: {n}")
        if n==0: break
        acts=pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');
          return [...r.querySelectorAll('button')].map(b=>({t:b.textContent.trim(),dis:/disabled/.test(b.className)}));}""")
        print("   store row buttons:", acts)
        r=pg.evaluate("""()=>{const row=document.querySelector('.md-dialog--full-page .md-table-row.table-row');
          const del=[...row.querySelectorAll('button')].find(b=>/delete|remove/i.test(b.textContent)&&!/disabled/.test(b.className));
          if(!del)return 'no-enabled-delete'; del.click(); return 'clicked';}""")
        pg.wait_for_timeout(3500)
        txt=N.sub_text(pg) or ""
        print("   delete:", r, "| dialog:", txt[:90].replace("\n"," | "))
        if any(w in txt.lower() for w in ("sure","delete","remove")):
            pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
              const d=ds[ds.length-1];const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}""")
            pg.wait_for_timeout(7000)
        else:
            break
        pg.goto(AFF, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000); N.click_tab(pg,"Stores")
    # 2) now try the affiliate row delete
    pg.goto(N.BASE+"/portal/affiliate", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.search_grid(pg,"RegressionTest")
    st=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      if(!r)return null;
      return {row:r.innerText.replace(/\\s+/g,' ').trim().slice(0,60),
              btns:[...r.querySelectorAll('button')].map(b=>({t:b.textContent.trim(),dis:/md-text--disabled/.test(b.className)}))};}""")
    print("\n  affiliate row now:", st)
    if st:
        r=pg.evaluate("""()=>{const row=document.querySelector('.md-table-row.table-row');
          const del=[...row.querySelectorAll('button')].find(b=>/delete/i.test(b.textContent)&&!/md-text--disabled/.test(b.className));
          if(!del)return 'still-disabled'; del.click(); return 'clicked';}""")
        pg.wait_for_timeout(4000)
        txt=N.sub_text(pg) or ""
        print("   delete:", r, "| dialog:", txt[:90].replace("\n"," | "))
        if any(w in txt.lower() for w in ("sure","delete","remove")):
            pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
              const d=ds[ds.length-1];const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}""")
            pg.wait_for_timeout(8000)
    pg.goto(N.BASE+"/portal/affiliate", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    print("  affiliates remaining:", N.search_grid(pg,"RegressionTest"))
    b.close()
