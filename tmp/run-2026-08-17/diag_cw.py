import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    N.add_new_grid(pg); pg.wait_for_timeout(4000)
    print("=== STEP1 row structure ===")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');
      if(!r)return 'no row';
      return {{cls:r.className, html:r.outerHTML.slice(0,700)}};}}"""))
    print("\nradio-ish elements:", pg.evaluate(f"""()=>{{const d={N.SUB};
      return [...d.querySelectorAll('input[type=radio],[class*=radio],[role=radio]')].slice(0,6).map(e=>({{
        tag:e.tagName,cls:(e.className||'').toString().slice(0,60),id:e.id,vis:e.offsetParent!==null}}));}}"""))
    # try clicking radio via playwright
    print("\ntrying playwright click on first radio cell...")
    try:
        loc=pg.locator(".md-dialog:not(.md-dialog--full-page) .datatable--radioSelect").first
        print("  radioSelect count:", pg.locator(".md-dialog:not(.md-dialog--full-page) .datatable--radioSelect").count())
        loc.click(); pg.wait_for_timeout(2500)
    except Exception as e: print("  err", str(e)[:90])
    print("  Next enabled:", pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent));return b?!b.disabled:null;}}"""))
    # try clicking the row itself
    try:
        pg.locator(".md-dialog:not(.md-dialog--full-page) .md-table-row.table-row").first.click(); pg.wait_for_timeout(2500)
    except Exception as e: print("  row err", str(e)[:70])
    print("  Next enabled after row click:", pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent));return b?!b.disabled:null;}}"""))
    b.close()
