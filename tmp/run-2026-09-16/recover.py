import sys, os; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
DL="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence/recover"; os.makedirs(DL,exist_ok=True)
def settle(pg,n,s=120):
    for _ in range(int(s/3)):
        pg.wait_for_timeout(3000)
        if n in pg.inner_text("body"): return True
    return False
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050},accept_downloads=True)
    pg=ctx.new_page()

    # --- 1. Export the Plans grid to CSV: does it include the deleted/inactive row? ---
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
    settle(pg,"Filter Plans"); pg.wait_for_timeout(8000)
    print("pagination:", pg.evaluate("""()=>{const m=document.body.innerText.match(/1-\\d+ of \\d+/);return m?m[0]:'?';}"""), flush=True)
    try:
        with pg.expect_download(timeout=60000) as di:
            pg.get_by_text("Export as CSV").first.click()
        d=di.value; path=DL+"/plans_export.csv"; d.save_as(path)
        print("EXPORT saved:", path, os.path.getsize(path), "bytes", flush=True)
    except Exception as e:
        print("EXPORT failed:", str(e)[:120], flush=True)

    # --- 2. Plans grid filter: is there a Status/Active column exposing inactive rows? ---
    try:
        pg.get_by_text("Filter Plans").first.click(); pg.wait_for_timeout(5000)
        cols=N.rs_open_ph(pg,"Select a filter")
        print("FILTER COLUMNS:", cols, flush=True)
    except Exception as e:
        print("filter probe failed:", str(e)[:100], flush=True)

    # --- 3. Global timeline: is the delete logged, with any prior values? ---
    pg.goto(N.BASE+"/portal/timeline", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(30000)
    t=pg.inner_text("body")
    print("\n=== GLOBAL TIMELINE (first 1800 chars) ===", flush=True)
    print(t[:1800].replace("\n"," | "), flush=True)
    pg.screenshot(path=DL+"/timeline.png", full_page=True)
    b.close()
