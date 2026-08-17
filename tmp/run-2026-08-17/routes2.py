from playwright.sync_api import sync_playwright
import json
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
NAV=["Users","Customers","Calls","Registrations","Purchase","Repair Shops","Affiliates","Claim Reports","Timeline"]
out={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050})
    pg=ctx.new_page()
    for item in NAV:
        try:
            pg.goto(BASE+"/portal/dashboard", wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(6000)
            el=pg.get_by_text(item, exact=True)
            if el.count()==0:
                out[item]="(nav item not found)"; print(f"  {item:16s} -> NOT FOUND"); continue
            el.first.click()
            pg.wait_for_timeout(7000)
            rows=pg.locator(".md-table-row").count()
            lost="LOOKS LIKE YOU'RE LOST" in pg.inner_text("body")
            out[item]={"url":pg.url,"rows":rows,"lost":lost}
            print(f"  {item:16s} -> {pg.url}   rows={rows} lost={lost}")
        except Exception as e:
            out[item]=f"ERR {str(e)[:60]}"; print(f"  {item:16s} -> ERR {str(e)[:60]}")
    json.dump(out, open(EV+"/routes.json","w"), indent=1)
    b.close()
