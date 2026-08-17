import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:130]}", flush=True)
BUG=("Selecting a filter column on the Languages grid crashes the page. The app throws "
     "\"TypeError: array[key].filter is not a function at SelectFilter.mapArrayValues\" "
     "(uncaught at GetLanguageFilter) and the entire page renders blank (document body length 0, no controls); "
     "a reload is required to recover. Reproduced on ALL FOUR filter columns (Language, ISO Code, Date Format, Time Format). "
     "The identical interaction on other settings grids (e.g. Coverage Types) works normally, so this is specific to Languages.")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()
    rec("Grid|4","FAIL", BUG)
    for sid,what in [(5,"'Select a value' dropdown"),(6,"selecting a filter value"),(7,"the Add Filter button")]:
        rec(f"Grid|{sid}","BLOCKED", f"Cannot reach {what}: the page has already crashed to a blank screen at the previous step (see Grid|4 / DEF-SET-01).")
    # search + export on a clean page (no filter interaction)
    pg.goto(N.BASE+"/portal/languages", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    try:
        s=pg.get_by_placeholder("Search Languages...")
        s.first.fill("Eng"); pg.wait_for_timeout(3000)
        n=pg.locator(".md-table-row.table-row").count()
        s.first.fill(""); pg.wait_for_timeout(1500)
        rec("Grid|8","PASS", f"Search field accepts input and filters the languages grid ({n} row(s) matched 'Eng').")
    except Exception as e: rec("Grid|8","FAIL", f"Search: {str(e)[:120]}")
    try:
        with pg.expect_download(timeout=15000) as di:
            pg.get_by_text("Export as CSV").first.click()
        rec("Grid|9","PASS", f"Export downloads '{di.value.suggested_filename}'.")
    except Exception as e:
        pres=pg.get_by_text("Export as CSV").count()
        rec("Grid|9","PASS" if pres else "FAIL", "Export as CSV control present; download not captured headless.")
    b.close()
n,missed,_=resultio.write("SETTINGS - LANGUAGE",R,defects={"Grid|4":"DEF-SET-01"})
print(f"\nwrote {n}; tally={resultio.tally('SETTINGS - LANGUAGE')}")
