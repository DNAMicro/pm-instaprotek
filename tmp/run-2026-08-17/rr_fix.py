import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
R={}
def rec(k,s,n): R[k]=(s,n[:440]); print(f"  {k}: {s} — {n[:140]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(9500)
    N.click_tab(pg,"Repair Receipt"); pg.wait_for_timeout(4500)
    pg.evaluate("""()=>{const c=document.querySelector('#is_customer_using_insurance');
      if(c&&!c.checked)(c.closest('label')||c).click();}""")
    pg.wait_for_timeout(3500)
    # real Playwright click on the device insurance select
    opts=[]
    try:
        sel=pg.locator(".md-dialog--full-page #device_insurance").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
        sel.scroll_into_view_if_needed(); sel.click(); pg.wait_for_timeout(2500)
        opts=N.opts(pg)
        if not opts:
            pg.locator(".md-dialog--full-page #device_insurance").click()
            pg.keyboard.press("ArrowDown"); pg.wait_for_timeout(2000); opts=N.opts(pg)
    except Exception as e: print("   err", str(e)[:80], flush=True)
    rec("Repair Receipt|3","PASS" if opts else "FAIL", f"Device Insurance field opens its options list: {opts}")
    pick=None
    if opts:
        try: pick=N.rs_pick(pg)
        except Exception as e: print("   pick err", str(e)[:60], flush=True)
    rec("Repair Receipt|4","PASS" if pick else "FAIL", f"Selected insurance option '{pick}' reflects on the field.")
    # covered amount via keyboard typing (currency-masked field)
    got=None; ok=False
    try:
        L=pg.locator(".md-dialog--full-page #covered_amount")
        L.scroll_into_view_if_needed(); L.click()
        pg.keyboard.press("Control+a"); pg.keyboard.type("15000")
        pg.wait_for_timeout(1200); got=L.input_value()
        ok = got not in (None,"","USD  0.00")
        # revert
        L.click(); pg.keyboard.press("Control+a"); pg.keyboard.type("0"); pg.wait_for_timeout(700)
    except Exception as e: got=str(e)[:70]
    rec("Repair Receipt|9","PASS" if ok else "FAIL",
        f"Covered amount field accepts input — field reads '{got}' after typing (currency-masked field). Value reverted, nothing saved.")
    b.close()
n,missed,_=resultio.write("CLAIM REPORTS",R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally("CLAIM REPORTS"))
