import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
COLS=["Language","ISO Code","Date Format","Time Format"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    for col in COLS:
        pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
        errs=[]
        pg.on("console", lambda m,E=errs: E.append(m.text[:110]) if m.type=="error" else None)
        pg.goto(N.BASE+"/portal/languages", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        pg.get_by_text("Filter Languages").first.click(); pg.wait_for_timeout(2200)
        try:
            N.rs_open_ph(pg,"Select a filter")
            pg.locator(".Select-menu-outer .Select-option", has_text=col).first.click()
            pg.wait_for_timeout(4500)
        except Exception as e:
            print(f"  {col:14s} -> interaction error {str(e)[:50]}"); pg.close(); continue
        body=pg.inner_text("body").strip()
        blank = len(body)==0
        print(f"  {col:14s} -> page blank={blank} bodylen={len(body)} err={errs[:1]}")
        pg.close()
    # control: does the same interaction work on another settings grid?
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/coverage-type", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.get_by_text("Filter Coverage Types").first.click(); pg.wait_for_timeout(2200)
    N.rs_open_ph(pg,"Select a filter"); pg.locator(".Select-menu-outer .Select-option").first.click(); pg.wait_for_timeout(4000)
    print(f"  [control] coverage-type filter -> bodylen={len(pg.inner_text('body').strip())} (non-zero = page fine)")
    b.close()
