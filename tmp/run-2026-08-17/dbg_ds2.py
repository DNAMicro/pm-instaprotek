import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
DEV="""()=>{const ts=[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')];
  const t=ts.find(x=>/Device Name/.test(x.innerText));
  if(!t)return {n:-1,names:[]};
  const rs=[...t.querySelectorAll('.md-table-row.table-row')];
  return {n:rs.length,names:rs.slice(0,4).map(r=>r.innerText.replace(/check_box_outline_blank/g,'').replace(/\\s+/g,' ').trim().slice(0,26))};}"""
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    N.click_tab(pg,"Devices"); N.add_new_in_record(pg)
    pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');
      const cb=r.querySelector('input[type=checkbox],input[type=radio]');(cb?(cb.closest('label')||cb):r).click();}}""")
    pg.wait_for_timeout(2000); N.sub_click(pg,"Next"); pg.wait_for_timeout(8000)
    base=pg.evaluate(DEV); print("baseline:", base)
    box=pg.get_by_placeholder("Search Devices...")
    box=(box.last if box.count()>1 else box.first)
    for term in ["100e","14e","zzzzz"]:
        box.fill(""); pg.wait_for_timeout(2000)
        box.fill(term)
        for w in (3,6,10):
            pg.wait_for_timeout(3000)
            r=pg.evaluate(DEV)
            print(f"  {term!r} @{w}s -> n={r['n']} names={r['names'][:3]}")
    N.sub_click(pg,"Cancel")
    b.close()
