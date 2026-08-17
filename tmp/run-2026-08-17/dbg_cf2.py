import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/coverage-type", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    n0=pg.evaluate("""()=>document.querySelectorAll('.dnaTable2-headerSet-item').length""")
    print("headerSet items:", n0, pg.evaluate("""()=>[...document.querySelectorAll('.dnaTable2-headerSet-item')].map(e=>e.innerText.trim().slice(0,20))"""))
    # click a Custom Filter tab and look for controls
    pg.evaluate("""()=>{const els=[...document.querySelectorAll('.dnaTable2-headerSet-item')].filter(e=>/Custom Filter/.test(e.innerText));
      if(els.length)els[0].click();}""")
    pg.wait_for_timeout(3500)
    print("\nafter clicking a Custom Filter tab:")
    print(" html of that item:", pg.evaluate("""()=>{const e=[...document.querySelectorAll('.dnaTable2-headerSet-item')].find(x=>/Custom Filter/.test(x.innerText));
      return e?e.outerHTML.slice(0,400):null;}"""))
    print(" nearby buttons:", pg.evaluate("""()=>[...document.querySelectorAll('button,i.material-icons')].filter(e=>e.offsetParent!==null&&/close|delete|clear|remove/i.test(e.textContent)).map(e=>e.textContent.trim()).slice(0,10)"""))
    print(" 'Filter Set' controls:", pg.evaluate("""()=>[...document.querySelectorAll('*')].filter(e=>/Filter Set/.test(e.textContent)&&e.children.length<3).map(e=>({t:e.textContent.trim().slice(0,30),tag:e.tagName})).slice(0,5)"""))
    b.close()
