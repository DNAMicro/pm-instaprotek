import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    N.add_new_grid(pg); pg.wait_for_timeout(4500)
    print("BEFORE selection — step section visibility:")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};
      return [...d.querySelectorAll('h1,h2,h3,h4,.md-title,.md-subheading-1,.md-subheading-2')]
        .filter(e=>/Step \\d/.test(e.textContent))
        .map(e=>({{txt:e.textContent.trim().slice(0,34), visible:e.offsetParent!==null,
                  rect:Math.round(e.getBoundingClientRect().height)}}));}}"""))
    pg.locator(".md-dialog:not(.md-dialog--full-page) .datatable--radioSelect").first.click(); pg.wait_for_timeout(2500)
    print("\nAFTER selection:")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};
      return [...d.querySelectorAll('h1,h2,h3,h4,.md-title,.md-subheading-1,.md-subheading-2')]
        .filter(e=>/Step \\d/.test(e.textContent))
        .map(e=>({{txt:e.textContent.trim().slice(0,34), visible:e.offsetParent!==null,
                  h:Math.round(e.getBoundingClientRect().height)}}));}}"""))
    print("\nsection content sample (Step 2 area):")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};
      const h=[...d.querySelectorAll('*')].find(e=>/Step 2Product Details/.test(e.textContent)&&e.children.length<5);
      if(!h)return 'not found';
      const sec=h.closest('section,div');
      return sec?sec.innerText.slice(0,200).replace(/\\n/g,' | '):'no section';}}"""))
    r=pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);
      if(b){{b.click();return 'clicked';}}return 'no';}}""")
    pg.wait_for_timeout(6000)
    print("\nAFTER Next — full modal text (first 700):")
    print(N.sub_text(pg)[:700].replace("\n"," | "))
    print("\nbuttons now:", N.sub_btns(pg)[-6:])
    print("\n>>> NOT clicking Yes (would submit a real claim). Cancelling.")
    pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/No/.test(x.textContent));if(b)b.click();}}""")
    pg.wait_for_timeout(2500)
    N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)
    b.close()
