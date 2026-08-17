import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
def devrows(pg):
    return pg.evaluate("""()=>{const ts=[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')];
      const t=ts.find(x=>/Device Name/.test(x.innerText));
      return t?t.querySelectorAll('.md-table-row.table-row').length:-1;}""")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    N.click_tab(pg,"Devices"); N.add_new_in_record(pg)
    s=pg.get_by_placeholder("Search Brands...")
    s.first.fill("Apple"); pg.wait_for_timeout(4000)
    pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');
      const cb=r.querySelector('input[type=checkbox],input[type=radio]');(cb?(cb.closest('label')||cb):r).click();}}""")
    pg.wait_for_timeout(2000)
    N.sub_click(pg,"Next"); pg.wait_for_timeout(6000)
    print("device rows (no search):", devrows(pg))
    print("tables in modal:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')].map(t=>({hdr:t.innerText.slice(0,60).replace(/\\n/g,'|'),rows:t.querySelectorAll('.md-table-row.table-row').length}))"""))
    ds=pg.get_by_placeholder("Search Devices...")
    print("device search count:", ds.count())
    for term in ["i","iPhone","1"]:
        ds.first.fill(""); ds.first.fill(term); pg.wait_for_timeout(5000)
        print(f"  search {term!r} -> device rows={devrows(pg)}")
    ds.first.fill(""); pg.wait_for_timeout(3000)
    print("after clearing:", devrows(pg))
    r=pg.evaluate("""()=>{const ts=[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')];
      const t=ts.find(x=>/Device Name/.test(x.innerText));
      const row=t.querySelector('.md-table-row.table-row'); if(!row)return 'no-row';
      const cb=row.querySelector('input[type=checkbox]'); if(!cb)return 'no-cb';
      (cb.closest('label')||cb).click(); return cb.checked?'checked':'clicked';}""")
    pg.wait_for_timeout(2500)
    print("select device ->", r)
    print("buttons:", N.sub_btns(pg)[-4:])
    print("save enabled:", pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent));return b?!b.disabled:null;}}"""))
    N.sub_click(pg,"Cancel")
    b.close()
