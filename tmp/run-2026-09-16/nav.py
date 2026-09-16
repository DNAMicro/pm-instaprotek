from playwright.sync_api import sync_playwright
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence"
B="https://crm.instaprotek.com"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=EV+"/auth_state.json", viewport={"width":1600,"height":1000})
    pg=ctx.new_page()
    pg.goto(B+"/portal/dashboard", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(6000)
    links=pg.evaluate("()=>[...document.querySelectorAll('a[href]')].map(a=>[a.textContent.trim().slice(0,30),a.getAttribute('href')]).filter(x=>x[1].includes('/portal'))")
    for t,h in links: print(f"NAV  {t:30s} {h}")
    # expand Settings submenu
    pg.evaluate("()=>{const e=[...document.querySelectorAll('*')].find(x=>x.children.length===0&&x.textContent.trim()==='Settings');if(e)e.click();}")
    pg.wait_for_timeout(3000)
    links2=pg.evaluate("()=>[...document.querySelectorAll('a[href]')].map(a=>[a.textContent.trim().slice(0,30),a.getAttribute('href')]).filter(x=>x[1].includes('/portal'))")
    print("--- after settings expand ---")
    for t,h in links2: print(f"SET  {t:30s} {h}")
    pg.screenshot(path=EV+"/nav.png", full_page=False)
    b.close()
