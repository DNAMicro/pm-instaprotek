import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(9500)
    N.click_tab(pg,"Repair Receipt"); pg.wait_for_timeout(4500)
    def show():
        return pg.evaluate("""()=>['repair_amount','covered_amount'].reduce((o,id)=>{const e=document.querySelector('#'+id);
          o[id]=e?{val:e.value,dis:e.disabled,ro:e.readOnly,max:e.getAttribute('maxlength'),pat:e.getAttribute('pattern')}:null;return o;},{})""")
    print("initial:", show())
    # 1) type into repair_amount first
    L=pg.locator(".md-dialog--full-page #repair_amount")
    L.click(); pg.keyboard.press("Control+a"); pg.keyboard.type("250"); pg.wait_for_timeout(1200)
    print("after repair_amount type:", show())
    # 2) now covered_amount, char by char
    C=pg.locator(".md-dialog--full-page #covered_amount")
    C.click(); pg.wait_for_timeout(500)
    pg.keyboard.press("Control+a"); pg.keyboard.press("Backspace"); pg.wait_for_timeout(400)
    print("after clearing covered:", show())
    for ch in "150":
        pg.keyboard.type(ch); pg.wait_for_timeout(400)
    print("after typing 150 into covered:", show())
    # 3) try .fill
    try:
        C.fill("175"); pg.wait_for_timeout(1000)
    except Exception as e: print("fill err", str(e)[:60])
    print("after fill:", show())
    # is it recalculated by something?
    print("\ncovered_amount outerHTML:", pg.evaluate("""()=>{const e=document.querySelector('#covered_amount');return e?e.outerHTML.slice(0,300):null;}"""))
    b.close()
