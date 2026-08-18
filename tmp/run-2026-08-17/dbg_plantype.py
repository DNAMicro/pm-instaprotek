import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.add_new_grid(pg)
    print("STEP1 full text:")
    print(N.sub_text(pg)[:700].replace("\n"," | "))
    print("\ncontrols:", [ (c['id'],c['label'],c['type']) for c in S.controls(pg) ])
    print("\nselect placeholders:", pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('.Select')].map(s=>
      (s.querySelector('.Select-placeholder')||{{}}).textContent||(s.querySelector('.Select-value-label')||{{}}).textContent||null);}}"""))
    print("\nany 'Single'/'Multiple' text:", pg.evaluate(f"""()=>{{const d={N.SUB};const t=d.innerText;
      return ['Single','Multiple','Bundle','Plan Type'].filter(k=>t.includes(k));}}"""))
    N.sub_click(pg,"Cancel")
    b.close()
