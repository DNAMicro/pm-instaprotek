from playwright.sync_api import sync_playwright
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence"
B="https://crm.instaprotek.com"
ITEMS=["Repair Shops","Claim Reports","Product Reviews","Device Buyback","Timeline","Purchase"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=EV+"/auth_state.json", viewport={"width":1600,"height":1000})
    pg=ctx.new_page()
    for it in ITEMS:
        pg.goto(B+"/portal/dashboard", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(5000)
        r=pg.evaluate(f"""()=>{{const els=[...document.querySelectorAll('li,div,span,a,button')]
            .filter(e=>e.textContent.trim()==='{it}'&&e.offsetParent!==null);
          if(!els.length)return 'nf';els[els.length-1].click();return 'ok';}}""")
        pg.wait_for_timeout(6000)
        rows=pg.evaluate("()=>document.querySelectorAll('.md-table-row.table-row, tbody tr').length")
        print(f"{it:16s} {r} -> {pg.url[len(B):]:30s} rows={rows}")
    # settings submenu
    pg.goto(B+"/portal/dashboard", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(5000)
    pg.evaluate("()=>{const els=[...document.querySelectorAll('li,div,span,a,button')].filter(e=>e.textContent.trim()==='Settings'&&e.offsetParent!==null);if(els.length)els[els.length-1].click();}")
    pg.wait_for_timeout(3500)
    print("SETTINGS SUBMENU:", pg.evaluate("()=>[...document.querySelectorAll('li,a,span')].map(e=>e.textContent.trim()).filter(t=>t&&t.length<30&&e=>1).slice(0,0)"))
    txt=pg.inner_text("body")
    print("BODY-NAV:", txt[:1200])
    b.close()
