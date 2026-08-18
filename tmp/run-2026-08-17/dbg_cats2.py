import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    print("tabs:", N.tabs(pg))
    print("clicked Products:", N.click_tab(pg,"Products"))
    n=N.add_new_in_record(pg)
    print("add_new clicked n=", n, "| sub modal open:", N.has_sub(pg))
    print("modal head:", (N.sub_text(pg) or '')[:120].replace("\n"," | "))
    # JS-click the categories Select-control (multi-select)
    r=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return 'no-modal';
      const e=d.querySelector('#categories'); if(!e)return 'no-categories';
      const s=e.closest('.Select'); s.scrollIntoView({{block:'center'}});
      const c=s.querySelector('.Select-control'); if(!c)return 'no-control';
      c.click(); return 'clicked';}}""")
    pg.wait_for_timeout(2500)
    print("categories open ->", r, "options:", N.opts(pg)[:10])
    if not N.opts(pg):
        pg.evaluate(f"""()=>{{const d={N.SUB};const e=d.querySelector('#categories');
          e.focus(); const ev=new KeyboardEvent('keydown',{{key:'ArrowDown',keyCode:40,bubbles:true}}); e.dispatchEvent(ev);}}""")
        pg.wait_for_timeout(2500)
        print("after ArrowDown:", N.opts(pg)[:10])
    b.close()
