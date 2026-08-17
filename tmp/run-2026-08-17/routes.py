from playwright.sync_api import sync_playwright
import json
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/dashboard", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(8000)
    links=pg.evaluate("""()=>[...document.querySelectorAll('a[href]')].map(a=>[a.textContent.trim().replace(/\\s+/g,' '),a.getAttribute('href')]).filter(x=>x[1]&&x[1].includes('/'))""")
    seen={}
    for t,h in links:
        if h not in seen and t: seen[h]=t
    for h,t in seen.items(): print(f"  {t[:34]:36s} -> {h}")
    json.dump(seen, open(EV+"/routes.json","w"), indent=1)
    # expand Settings menu too
    try:
        pg.get_by_text("Settings").first.click(); pg.wait_for_timeout(3000)
        l2=pg.evaluate("""()=>[...document.querySelectorAll('a[href]')].map(a=>[a.textContent.trim(),a.getAttribute('href')])""")
        extra={h:t for t,h in l2 if h and h not in seen and t}
        print("--- after opening Settings ---")
        for h,t in extra.items(): print(f"  {t[:34]:36s} -> {h}")
        seen.update(extra); json.dump(seen, open(EV+"/routes.json","w"), indent=1)
    except Exception as e: print("settings expand:",str(e)[:80])
    b.close()
