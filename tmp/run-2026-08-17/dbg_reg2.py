import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/regions", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    print("existing regions:", pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.split('\\n')[0].trim())"""))
    N.add_new_grid(pg)
    pg.evaluate(f"""()=>{{const d={N.SUB};const s=d.querySelector('.Select');if(s){{s.scrollIntoView({{block:'center'}});s.querySelector('.Select-control').click();}}}}""")
    for w in (2,5,9):
        pg.wait_for_timeout(3000)
        o=N.opts(pg)
        noresult=pg.evaluate("""()=>{const m=document.querySelector('.Select-menu-outer');return m?m.innerText.slice(0,80):null;}""")
        print(f"  after ~{w}s: options={o} menu={noresult!r}")
    b.close()
