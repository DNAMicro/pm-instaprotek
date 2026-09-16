import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
R={"Device Category":"/portal/category","Product Category":"/portal/product-category","Brand":"/portal/brand",
"Registration Survey":"/portal/survey","Plans":"/portal/product-plans","Company":"/portal/company",
"Repair Network":"/portal/repair-network","Languages":"/portal/languages","Regions":"/portal/regions",
"Administrators":"/portal/administrators","Underwriters":"/portal/underwriters","Support":"/portal/support",
"Coverage Type":"/portal/coverage-type","Coverage Cost Type":"/portal/coverage-cost-type",
"Share":"/portal/share/product","Review Questions":"/portal/review-questions",
"Users":"/portal/user","Customers":"/portal/customer","Registrations":"/portal/registration",
"Repair Shops":"/portal/shop","Affiliates":"/portal/affiliate","Claim Reports":"/portal/claim",
"Product Reviews":"/portal/product-review","Device Buyback":"/portal/buy-back","Orders":"/portal/order",
"Purchase":"/portal/purchase","Calls":"/portal/call"}
out={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1050}).new_page()
    for k,r in R.items():
        try:
            pg.goto(N.BASE+r, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(6500)
            rows=pg.locator(".md-table-row.table-row").count()
            body=pg.inner_text("body")
            lost="LOOKS LIKE YOU'RE LOST" in body.upper()
            fl=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Filter /.test(x.textContent));return b?b.textContent.trim():null;}""")
            an=pg.get_by_text("addNew").count()
            out[k]={"url":r,"rows":rows,"lost":lost,"filter":fl,"addNew":an}
            print(f"{k:22s} {r:28s} rows={rows:3d} lost={lost} new={an} filter={fl}", flush=True)
        except Exception as e:
            out[k]={"err":str(e)[:60]}; print(f"{k:22s} ERR {str(e)[:60]}", flush=True)
    json.dump(out, open(N.EV+"/routes.json","w"), indent=1)
    b.close()
