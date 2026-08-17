import json, re, time
from playwright.sync_api import sync_playwright
c=json.load(open('/home/farsheed/pm-instaprotek/credentials.json'))
D="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence/"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=D+"auth_state.json",viewport={'width':1600,'height':1000})
    pg=ctx.new_page()
    for i in range(3):
        pg.goto("https://crm.nullnet.instaprotek.com/portal/dashboard",wait_until="domcontentloaded",timeout=60000)
        pg.wait_for_timeout(7000)
        t=pg.inner_text("body")
        m=re.findall(r"Total (?:Registrations|Claims): ([\d,]+)",t)[:2]
        print(f"  reading {i+1} @ {time.strftime('%H:%M:%S')}: registrations={m[0] if m else '?'}  claims={m[1] if len(m)>1 else '?'}")
        if i<2: time.sleep(30)
    # recent registrations
    pg.goto("https://crm.nullnet.instaprotek.com/portal/registration",wait_until="domcontentloaded",timeout=60000)
    pg.wait_for_timeout(9000)
    rows=pg.locator(".md-table-row.table-row")
    print("\n  registration grid rows:",rows.count())
    for i in range(min(5,rows.count())):
        print("   ",rows.nth(i).inner_text().replace("\n"," | ")[:190])
    pg.screenshot(path=D+"registrations_grid.png",full_page=False)
    b.close()
