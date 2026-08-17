import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
    pg.on("console", lambda m: errs.append("console:"+m.text[:100]) if m.type=="error" else None)
    pg.goto(N.BASE+"/portal/languages", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    pg.get_by_text("Filter Languages").first.click(); pg.wait_for_timeout(2500)
    N.rs_open_ph(pg,"Select a filter")
    pg.locator(".Select-menu-outer .Select-option", has_text="Language").first.click()
    pg.wait_for_timeout(5000)
    print("URL:", pg.url)
    print("BODY:", pg.inner_text("body")[:400].replace("\n"," | "))
    print("\nbuttons:", pg.evaluate("()=>[...document.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean).slice(0,20)"))
    print("\nJS errors:", errs[:6])
    b.close()
