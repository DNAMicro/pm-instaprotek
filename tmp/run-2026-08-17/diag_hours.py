import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
SHOP_URL=json.load(open(N.EV+"/shop_ctx.json"))["shop_url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(SHOP_URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Branches"); N.add_new_in_record(pg)
    N.rs_open_ph(pg,"Operating Days"); N.rs_pick(pg,"Monday"); pg.wait_for_timeout(2500)
    print("=== operating hours HTML ===")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};const t=d.innerText;const i=t.indexOf('Operating Hours');
      const el=[...d.querySelectorAll('*')].find(e=>/Operating Hours/.test(e.textContent)&&e.children.length<8);
      const box=el?el.closest('.md-cell,div').parentElement:null;
      return box?box.innerHTML.slice(0,1500):'not found';}}"""))
    print("\n=== click select #1 then look for ANY popup ===")
    pg.evaluate(f"""()=>{{const d={N.SUB};const s=[...d.querySelectorAll('.Select')][1];if(s){{s.scrollIntoView({{block:'center'}});s.click();}}}}""")
    pg.wait_for_timeout(2500)
    print("Select-menu-outer count:", pg.locator(".Select-menu-outer").count())
    print("md-layover options:", pg.evaluate("()=>[...document.querySelectorAll('.md-list.md-layover-child [role=option]')].map(e=>e.textContent.trim()).slice(0,12)"))
    print("any listbox:", pg.evaluate("()=>[...document.querySelectorAll('[role=listbox],[role=menu],.md-list')].map(e=>({cls:e.className.slice(0,40),n:e.children.length,txt:e.innerText.slice(0,60).replace(/\\n/g,'|')})).slice(0,6)"))
    print("select#1 classes:", pg.evaluate(f"""()=>{{const d={N.SUB};const s=[...d.querySelectorAll('.Select')][1];return s?s.className:null;}}"""))
    print("select#1 html:", pg.evaluate(f"""()=>{{const d={N.SUB};const s=[...d.querySelectorAll('.Select')][1];return s?s.outerHTML.slice(0,600):null;}}"""))
    b.close()
