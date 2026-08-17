import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    N.click_tab(pg,"Devices"); N.add_new_in_record(pg)
    print("STEP1 buttons:", N.sub_btns(pg))
    print("STEP1 search inputs:", pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('input')].map(e=>({{id:e.id,ph:e.placeholder,type:e.type,vis:e.offsetParent!==null}})).slice(0,6);}}"""))
    pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');
      const cb=r.querySelector('input[type=checkbox],input[type=radio]');(cb?(cb.closest('label')||cb):r).click();}}""")
    pg.wait_for_timeout(2000)
    print("\nclick Next ->", N.sub_click(pg,"Next")); pg.wait_for_timeout(5500)
    print("STEP2 text:", N.sub_text(pg)[:200].replace("\n"," | "))
    print("STEP2 buttons:", N.sub_btns(pg))
    print("STEP2 inputs:", pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('input')].map(e=>({{id:e.id,ph:e.placeholder,type:e.type,vis:e.offsetParent!==null}})).slice(0,6);}}"""))
    print("STEP2 rows:", pg.evaluate(f"""()=>{{const d={N.SUB};return d.querySelectorAll('.md-table-row.table-row').length;}}"""))
    print("\ncancel ->", N.sub_click(pg,"Cancel"))
    b.close()
