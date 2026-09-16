from playwright.sync_api import sync_playwright
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence"
B="https://crm.instaprotek.com"
CAND=["/portal/users","/portal/user","/portal/customers","/portal/customer","/portal/calls","/portal/call",
"/portal/registrations","/portal/registration","/portal/purchase","/portal/orders","/portal/order",
"/portal/repair-shops","/portal/repairshops","/portal/repair-shop","/portal/affiliates","/portal/affiliate",
"/portal/claim-reports","/portal/claimreports","/portal/claim-report","/portal/product-reviews",
"/portal/device-buyback","/portal/settings","/portal/timeline","/portal/dashboard"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=EV+"/auth_state.json", viewport={"width":1600,"height":1000})
    pg=ctx.new_page()
    for r in CAND:
        try:
            pg.goto(B+r, wait_until="domcontentloaded", timeout=40000); pg.wait_for_timeout(3500)
            t=pg.inner_text("body")
            rows=pg.evaluate("()=>document.querySelectorAll('.md-table-row.table-row, tbody tr').length")
            shell=pg.evaluate("()=>({full:document.querySelectorAll('.md-dialog--full-page').length,adv:document.querySelectorAll('.advancedFullDialog').length})")
            bad = "404" in t[:200] or "not found" in t[:200].lower()
            print(f"{r:32s} -> {pg.url[len(B):]:34s} rows={rows:4d} bad={bad} shell={shell}")
        except Exception as e:
            print(f"{r:32s} -> ERR {str(e)[:70]}")
    b.close()
