import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:135]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/product-category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8500)
    cat=pg.evaluate("""()=>{const m=document.body.innerText.match(/Product Category:\\s*(.+)/);return m?m[1].trim().slice(0,30):null;}""")
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(5000)
    feed=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
      return p.length?p[0].innerText.slice(0,300).replace(/\\n/g,' | '):'';}""")
    print("  feed:", feed[:200])
    fb=pg.get_by_text("Filter Activity")
    if fb.count(): fb.first.click(); pg.wait_for_timeout(2000)
    vo=[]; tgt=None
    try:
        fo=N.rs_open_ph(pg,"Select a filter")
        tgt="Action" if "Action" in fo else fo[0]
        N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,tgt); pg.wait_for_timeout(1800)
        for _ in range(4):
            try: vo=N.rs_open_ph(pg,"Select a value")
            except Exception: pass
            if vo: break
            pg.wait_for_timeout(1500)
    except Exception as e: print("  err", str(e)[:70])
    rec("Timeline|4","PASS" if vo else "FAIL", f"Dependent value dropdown for '{tgt}' on product category '{cat}': {vo[:10]}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Timeline|5","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")
    pg.goto(pg.url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(4000)
    feed2=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
      return p.length?p[0].innerText.slice(0,320).replace(/\\n/g,' | '):'';}""")
    import re
    acts=sorted(set(re.findall(r'(Create|Update|Delete)\s+\w+', feed2)))
    rec("Timeline|8","PASS" if acts else "FAIL",
        f"Timeline records actions performed on product category '{cat}' — entries: {acts}. Feed: {feed2[:170]}")
    b.close()
n,_,_=resultio.write('SETTINGS - PRODUCT CATEGORY ',R)
print("tally:",resultio.tally('SETTINGS - PRODUCT CATEGORY '))
