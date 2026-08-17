import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/languages", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    pg.get_by_text("Filter Languages").first.click(); pg.wait_for_timeout(2500)
    N.rs_open_ph(pg,"Select a filter")
    # click option WITHOUT the generic helper, then inspect immediately
    opt=pg.locator(".Select-menu-outer .Select-option", has_text="Language").first
    print("option text:", opt.inner_text())
    opt.click()
    for w in (1,3,6):
        pg.wait_for_timeout(2000)
        st=pg.evaluate("""()=>({sels:[...document.querySelectorAll('.Select')].map(s=>({ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,val:s.querySelector('.Select-value-label')?.textContent.trim()||null})),
           hasVal:/Select a value/.test(document.body.innerText)})""")
        print(f"  +{w*2}s:", st)
    # reopen panel
    pg.get_by_text("Filter Languages").first.click(); pg.wait_for_timeout(2500)
    print("after reopening panel:", pg.evaluate("""()=>({sels:[...document.querySelectorAll('.Select')].map(s=>({ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,val:s.querySelector('.Select-value-label')?.textContent.trim()||null}))})"""))
    b.close()
