import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1900,'height':1200}).new_page()
    pg.goto(N.BASE+"/portal/review-questions", wait_until="domcontentloaded", timeout=90000)
    for _ in range(50):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    info=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const bs=[...r.querySelectorAll('button')].filter(e=>/edit|delete/.test(e.textContent));
      return bs.map(e=>({t:e.textContent.trim(), disabledProp:e.disabled,
        ariaDisabled:e.getAttribute('aria-disabled'), hasDisabledCls:/md-text--disabled/.test(e.className),
        pointerEvents:getComputedStyle(e).pointerEvents}));}""")
    print("row action buttons:")
    for i in info: print("   ", i)
    # compare against a grid where edit works, e.g. coverage-type
    pg.goto(N.BASE+"/portal/coverage-type", wait_until="domcontentloaded", timeout=90000)
    for _ in range(50):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    ctl=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const bs=[...r.querySelectorAll('button')].filter(e=>/edit|delete/.test(e.textContent));
      return bs.map(e=>({t:e.textContent.trim(), disabledProp:e.disabled,
        hasDisabledCls:/md-text--disabled/.test(e.className)}));}""")
    print("\ncontrol (coverage-type, where open works):")
    for i in ctl: print("   ", i)
    b.close()
