import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
SHOP_URL=json.load(open(N.EV+"/shop_ctx.json"))["shop_url"]
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:135]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(SHOP_URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Branches"); N.add_new_in_record(pg)
    N.rs_open_ph(pg,"Operating Days"); N.rs_pick(pg,"Monday"); pg.wait_for_timeout(2500)
    print("  sched classes:", pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('[class*=sched__]')].map(e=>e.className.match(/sched__\\w+/)[0]);}}"""))

    def open_time(cls):
        loc=pg.locator(f".md-dialog:not(.md-dialog--full-page) .{cls} .Select-control").first
        loc.scroll_into_view_if_needed(); loc.click(); pg.wait_for_timeout(1800)
        o=N.opts(pg)
        if not o:   # fallback: keyboard on the combobox
            pg.locator(f".md-dialog:not(.md-dialog--full-page) .{cls} .Select-input").first.click()
            pg.keyboard.press("ArrowDown"); pg.wait_for_timeout(1500); o=N.opts(pg)
        return o
    def val(cls):
        return pg.evaluate(f"""()=>{{const d={N.SUB};const s=d.querySelector('.{cls}');
          return s?(s.querySelector('.Select-value-label')?.textContent.trim()||''):null;}}""")

    am=open_time("sched__openTime")
    rec("Branches|15","PASS" if am else "FAIL", f"AM (opening) time field opens a dropdown of times: {am[:12]}{' …' if len(am)>12 else ''}")
    a=None
    if am:
        try: a=N.rs_pick(pg)
        except Exception as e: print("  pick err",str(e)[:50])
    rec("Branches|16","PASS" if (a and val("sched__openTime")) else "FAIL",
        f"Selected AM time '{a}' reflects on the field (field now reads '{val('sched__openTime')}').")
    pm=open_time("sched__closeTime")
    rec("Branches|17","PASS" if pm else "FAIL", f"PM (closing) time field opens a dropdown of times: {pm[:12]}{' …' if len(pm)>12 else ''}")
    c=None
    if pm:
        try: c=N.rs_pick(pg)
        except Exception as e: print("  pick err",str(e)[:50])
    rec("Branches|18","PASS" if (c and val("sched__closeTime")) else "FAIL",
        f"Selected PM time '{c}' reflects on the field (field now reads '{val('sched__closeTime')}').")
    N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2000)
    print("  [cleanup] modal cancelled — no extra branch created", flush=True)
    b.close()
n,missed,_=resultio.write("REPAIR SHOPS",R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally("REPAIR SHOPS"))
