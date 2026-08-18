import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N, setlib as S
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    N.click_tab(pg,"Products"); N.add_new_in_record(pg)
    print("modal text:", N.sub_text(pg)[:320].replace("\n"," | "))
    print("\nselects:", pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('.Select')].map((s,i)=>({{i,
      id:(s.querySelector('input')||{{}}).id||null,
      ph:(s.querySelector('.Select-placeholder')||{{}}).textContent||null}}));}}"""))
    print("\ncontrols:", [(c['id'],c['label'],c['type'],c['isSelect']) for c in S.controls(pg)])
    # open each select by id and list options
    for fid in ["plan","device_categories","product_category","responsible_claim_payer"]:
        if pg.locator(f".md-dialog:not(.md-dialog--full-page) #{fid}").count():
            try:
                o=N.rs_open(pg,fid,".md-dialog:not(.md-dialog--full-page)")
                print(f"  {fid}: {o[:8]}")
                if o: N.rs_pick(pg)
            except Exception as e: print(f"  {fid}: err {str(e)[:60]}")
        else:
            print(f"  {fid}: not present")
    b.close()
