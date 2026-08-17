import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
ITEMS=["Device Category","Product Category","Brand","Registration Survey","Plan","Repair Network",
       "Company","Language","Languages","Regions","Administrators","Underwriters","Support",
       "Coverage Type","Coverage Cost Type","Share","Review Questions"]
out={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/dashboard", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    # open the Settings menu
    pg.get_by_text("Settings", exact=True).first.click(); pg.wait_for_timeout(3500)
    menu=pg.evaluate("""()=>[...document.querySelectorAll('a,li,div,span')]
      .filter(e=>e.offsetParent!==null&&e.children.length<3&&e.textContent.trim().length<32)
      .map(e=>e.textContent.trim()).filter(Boolean)""")
    seen=[]
    for m in menu:
        if m not in seen: seen.append(m)
    print("visible menu entries after opening Settings:")
    print([m for m in seen if m][:70])
    b.close()
