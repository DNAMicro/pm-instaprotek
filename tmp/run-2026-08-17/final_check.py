import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
ROUTES=[("/portal/user","Users"),("/portal/shop","Repair Shops"),("/portal/affiliate","Affiliates"),
        ("/portal/category","Device Categories"),("/portal/product-category","Product Categories"),
        ("/portal/brand","Brands"),("/portal/product-plans","Plans"),("/portal/company","Companies"),
        ("/portal/coverage-type","Coverage Types"),("/portal/coverage-cost-type","Coverage Cost Types"),
        ("/portal/repair-network","Repair Network"),("/portal/regions","Regions"),
        ("/portal/administrators","Administrators"),("/portal/underwriters","Underwriters"),
        ("/portal/languages","Languages"),("/portal/support","Support"),
        ("/portal/share/product","Shares"),("/portal/review-questions","Review Questions"),
        ("/portal/survey","Registration Survey")]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    leftovers=[]
    for route,label in ROUTES:
        try:
            pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7000)
            hits=pg.evaluate("""()=>{const t=document.body.innerText;
              const rows=[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.replace(/\\s+/g,' ').trim());
              const inRows=rows.filter(x=>/RegressionTest/i.test(x));
              return {inRows, bodyHas:/RegressionTest/i.test(t)};}""")
            n=len(hits["inRows"])
            flag="LEFTOVER" if (n>0 or hits["bodyHas"]) else "clean"
            if n>0 or hits["bodyHas"]:
                leftovers.append((label, hits["inRows"][:2] or "(text match only)"))
            print(f"  {label:22s} {flag:9s} {hits['inRows'][:1]}")
        except Exception as e:
            print(f"  {label:22s} ERROR {str(e)[:60]}")
    print("\n=== LEFTOVERS ===")
    for l,r in leftovers: print(" ", l, "->", r)
    if not leftovers: print("  none — environment clean of RegressionTest records")
    b.close()
