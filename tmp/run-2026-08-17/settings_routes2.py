import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
ITEMS=["Device Category","Product Category","Brand","Registration Survey","Plans","Company",
       "Repair Network","Languages","Regions","Administrators","Underwriters","Support",
       "Coverage Type","Coverage Cost Type","Share","Review Questions"]
out={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for it in ITEMS:
        try:
            pg.goto(N.BASE+"/portal/dashboard", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(5500)
            pg.get_by_text("Settings", exact=True).first.click(); pg.wait_for_timeout(2000)
            pg.get_by_text(it, exact=True).first.click(); pg.wait_for_timeout(7000)
            rows=pg.locator(".md-table-row.table-row").count()
            lost="LOOKS LIKE YOU'RE LOST" in pg.inner_text("body")
            filt=[t for t in ["Filter "] if t in pg.inner_text("body")]
            fl=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Filter /.test(x.textContent));return b?b.textContent.trim():null;}""")
            out[it]={"url":pg.url,"rows":rows,"lost":lost,"filter":fl,
                     "addNew":pg.get_by_text("addNew").count()}
            print(f"  {it:22s} -> {pg.url.split('/portal')[-1]:28s} rows={rows:3d} new={out[it]['addNew']} filter={fl}")
        except Exception as e:
            out[it]={"err":str(e)[:70]}; print(f"  {it:22s} -> ERR {str(e)[:60]}")
    json.dump(out, open(N.EV+"/settings_routes.json","w"), indent=1)
    b.close()
