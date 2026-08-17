import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True).new_page()
    pg.goto(N.BASE+"/portal/languages", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    print("rows:", pg.locator(".md-table-row.table-row").count())
    print("search inputs:", pg.evaluate("""()=>[...document.querySelectorAll('input')].map(e=>({id:e.id,ph:e.placeholder,vis:e.offsetParent!==null}))"""))
    pg.get_by_text("Filter Languages").first.click(); pg.wait_for_timeout(2500)
    print("\nafter opening filter:")
    print(" body has 'Select a filter':", "Select a filter" in pg.inner_text("body"))
    print(" selects:", pg.evaluate("""()=>[...document.querySelectorAll('.Select')].map(s=>({ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,cls:s.className.slice(0,45)}))"""))
    o=N.rs_open_ph(pg,"Select a filter"); print(" filter options:", o)
    N.rs_pick(pg,"Language"); pg.wait_for_timeout(2500)
    print("\nafter picking Language:")
    print(" body has 'Select a value':", "Select a value" in pg.inner_text("body"))
    print(" selects:", pg.evaluate("""()=>[...document.querySelectorAll('.Select')].map(s=>({ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,val:s.querySelector('.Select-value-label')?.textContent.trim()||null}))"""))
    print(" panel text:", pg.evaluate("""()=>{const e=[...document.querySelectorAll('*')].find(x=>/Select a filter|No filter applied/.test(x.textContent)&&x.children.length<8);
      return e?e.innerText.slice(0,220).replace(/\\n/g,' | '):'';}"""))
    b.close()
