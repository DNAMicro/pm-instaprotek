"""Finish SETTINGS - PRODUCT CATEGORY: Products|1-8 (filters, on a populated real category,
read-only), Products|9-12 (no Add control exists), then Timeline/Notes on our own record
and teardown."""
import sys
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, set_record as SR
from playwright.sync_api import sync_playwright

SHEET="SETTINGS - PRODUCT CATEGORY "
TAG=SR.TAG
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:130]}", flush=True)

NOADD=("The Products tab of a Product Category record exposes no Add control at all — the only "
       "toolbar actions are 'Export as CSV' and 'Filter Products'. Verified on the newly created "
       "test category and on three real categories (Cables 27 products, Camera Lens 20, Case 24): "
       "no add/add_circle/New button is rendered in any of them. The test case expects an add button "
       "that opens an Add Products modal.")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()

    # ---- Products|1-8 on a populated REAL category (read-only) ----
    pg.goto(N.BASE+"/portal/product-category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9500)
    pg.evaluate("""()=>{const rows=[...document.querySelectorAll('.md-table-row.table-row')];
      const r=rows.find(x=>!/RegressionTest/.test(x.innerText))||rows[0];
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8500)
    cat=pg.evaluate("""()=>{const m=document.body.innerText.match(/Product Category:\\s*(.+)/);return m?m[1].trim().slice(0,30):null;}""")
    print(f"  [ctx] filters verified on real category '{cat}' (read-only)", flush=True)
    N.click_tab(pg,"Products")
    SR.filter_block(pg, rec, "Products", "Filter Products")

    # ---- Products|9-12 ----
    rec("Products|9","FAIL", NOADD)
    for sid,what in [(10,"searching for a product inside the Add Products modal"),
                     (11,"selecting a product"),
                     (12,"saving the selected products")]:
        rec(f"Products|{sid}","BLOCKED", f"Cannot reach {what}: the Add Products modal cannot be opened because no Add control exists on the Products tab (see Products|9 / DEF-SET-04).")

    # ---- Timeline + Notes on OUR record, then teardown ----
    pg.goto(N.BASE+"/portal/product-category", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
    found=N.search_grid(pg, TAG)
    if found>0:
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
        pg.wait_for_timeout(8500)
        url=pg.url
        print(f"  [ctx] own record {url.split('/portal')[-1]}", flush=True)
        SR.timeline_block(pg, rec, url)
        SR.notes_block(pg, rec, url)
        SR.teardown(pg, url, "/portal/product-category", SHEET.strip())
    else:
        print("  !! own test record not found", flush=True)

    b.close()

n,missed,_=resultio.write(SHEET,R,defects={"Products|9":"DEF-SET-04"})
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
