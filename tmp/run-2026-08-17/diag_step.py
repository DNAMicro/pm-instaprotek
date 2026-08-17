import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    N.add_new_grid(pg); pg.wait_for_timeout(4500)
    pg.locator(".md-dialog:not(.md-dialog--full-page) .datatable--radioSelect").first.click(); pg.wait_for_timeout(2500)
    for i in range(4):
        info=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
          const t=d.innerText;
          return {{allStepMatches:(t.match(/Step\\s*\\d/g)||[]),
                   head:t.slice(0,110).replace(/\\n/g,' | '),
                   activeStepper:[...d.querySelectorAll('[class*=step]')].filter(e=>/active|current|md-stepper--active/.test(e.className)).map(e=>e.className.slice(0,50)),
                   headings:[...d.querySelectorAll('h1,h2,h3,h4,.md-title,.md-subheading-1,.md-subheading-2')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,6),
                   btns:[...d.querySelectorAll('button')].map(x=>x.textContent.trim()).slice(-4)}};}}""")
        print(f"\n--- after {i} Next click(s) ---")
        for k,v in (info or {}).items(): print(f"   {k}: {v}")
        r=pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);
          if(b){{b.click();return 'clicked';}}return 'no-next';}}""")
        print("   next ->", r)
        if r=='no-next': break
        pg.wait_for_timeout(6500)
    b.close()
