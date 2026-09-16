import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
REC=[("product-category","29ba0fca-1ad7-4fd9-af02-f9bef8a87a49"),
     ("brand","c16268e4-4dac-44af-850d-8c9747e19b58")]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050}).new_page()
    for kind,rid in REC:
        pg.goto(f"{N.BASE}/portal/{kind}/{rid}", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(25000)
        t=pg.inner_text("body")
        shell=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')||document.querySelector('.advancedFullDialog');
          return d?d.innerText.slice(0,240).replace(/\\s+/g,' '):'(no record shell)';}""")
        print(f"\n=== {kind}/{rid}")
        print("  exists:", "No records found!" not in t)
        print("  shell :", shell)
        print("  ours? :", "RegressionTest0916" in t)
        pg.screenshot(path=N.EV+f"/touched_{kind}.png")
    b.close()
