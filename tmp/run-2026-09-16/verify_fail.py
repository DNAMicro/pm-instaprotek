"""Slow, deliberate re-verification of the suspect settings failures.
Each step waits generously and screenshots, so a timing artifact can be told
apart from a real product defect."""
import sys, json, os
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright

TN="VerifyTest0916"
EV=N.EV+"/verify"; os.makedirs(EV, exist_ok=True)
def bt(pg): return pg.inner_text("body")

def settle(pg, needle, secs=90):
    for _ in range(int(secs/3)):
        pg.wait_for_timeout(3000)
        if needle in bt(pg): return True
    return False

def report(tag, msg): print(f"  [{tag}] {msg}", flush=True)

def verify_languages_filter(pg):
    """Known-suspect: does choosing a filter column kill the Languages page?"""
    print("\n=== LANGUAGES: filter behaviour ===", flush=True)
    pg.goto(N.BASE+"/portal/languages", wait_until="domcontentloaded", timeout=90000)
    ok=settle(pg,"Filter Languages"); report("load", f"grid loaded={ok}, bodylen={len(bt(pg))}")
    pg.screenshot(path=EV+"/lang_1_grid.png")
    pg.get_by_text("Filter Languages").first.click(); pg.wait_for_timeout(6000)
    report("filter-open", f"'Select a filter' visible={'Select a filter' in bt(pg)}")
    pg.screenshot(path=EV+"/lang_2_panel.png")
    try:
        cols=N.rs_open_ph(pg,"Select a filter"); report("columns", cols)
    except Exception as e:
        report("columns", "ERR "+str(e)[:80]); cols=[]
    if cols:
        try:
            picked=N.rs_pick(pg, cols[0]); report("picked", picked)
        except Exception as e:
            report("picked","ERR "+str(e)[:80])
        pg.wait_for_timeout(9000)
        b=bt(pg)
        report("after-pick", f"bodylen={len(b)} | htmllen={pg.evaluate('()=>document.body.innerHTML.length')} | "
                            f"'Select a value' present={'Select a value' in b} | grid rows={pg.locator('.md-table-row.table-row').count()} | "
                            f"nav present={'Dashboard' in b}")
        pg.screenshot(path=EV+"/lang_3_afterpick.png")
        print("   BODY AFTER PICK:", b[:400].replace("\n"," | "), flush=True)

def verify_create(pg, route, filt, label, name_id=None):
    """Create a record slowly and confirm by reloading the grid and searching for it."""
    print(f"\n=== {label}: create -> reload -> search ===", flush=True)
    pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000)
    report("load", f"grid loaded={settle(pg,filt)}")
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(12000)
    report("modal", f"dialog count={pg.locator('.md-dialog').count()}")
    try:
        inp=pg.locator(".md-dialog input[type=text]:not([id*=search]):not([id*=Search])").first
        inp.fill(TN); pg.wait_for_timeout(1500)
        report("name", f"typed='{inp.input_value()}'")
    except Exception as e:
        report("name","ERR "+str(e)[:90])
    pg.screenshot(path=EV+f"/{label}_1_form.png")
    try:
        sb=pg.locator(".md-dialog button").filter(has_text="Save").first
        report("savebtn", f"text='{sb.inner_text().strip()}' enabled={sb.is_enabled()}")
        sb.click(timeout=30000)
    except Exception as e:
        report("savebtn","ERR "+str(e)[:90])
    pg.wait_for_timeout(15000)
    b=bt(pg)
    toast=[l.strip() for l in b.split("\n") if any(k in l.lower() for k in ("success","created","saved","error","required","invalid"))][:4]
    report("after-save", f"dialog still open={pg.locator('.md-dialog').count()>0} | messages={toast}")
    pg.screenshot(path=EV+f"/{label}_2_aftersave.png")
    # ground truth: reload the grid and search
    pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000); settle(pg,filt)
    try:
        s=pg.locator("input[placeholder*='Search']").first
        s.fill(TN); pg.wait_for_timeout(12000)
        n=pg.locator(".md-table-row.table-row").count()
        report("VERDICT", f"after reload+search '{TN}' -> {n} matching row(s) => created={n>0}")
        pg.screenshot(path=EV+f"/{label}_3_search.png")
        return n>0
    except Exception as e:
        report("VERDICT","ERR "+str(e)[:90]); return None

def cleanup(pg, route, filt, label):
    pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000); settle(pg,filt)
    try:
        s=pg.locator("input[placeholder*='Search']").first; s.fill(TN); pg.wait_for_timeout(10000)
        if pg.locator(".md-table-row.table-row").count()==0:
            report("cleanup","nothing to delete"); return True
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const d=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete/.test(e.textContent));if(d)d.click();}""")
        pg.wait_for_timeout(6000)
        report("cleanup-confirm", bt(pg)[-260:].replace("\n"," | "))
        pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];const d=ds[ds.length-1];
          const b=[...d.querySelectorAll('button')].find(x=>/Yes/i.test(x.textContent));if(b)b.click();}""")
        pg.wait_for_timeout(10000)
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000); settle(pg,filt)
        s=pg.locator("input[placeholder*='Search']").first; s.fill(TN); pg.wait_for_timeout(10000)
        left=pg.locator(".md-table-row.table-row").count()
        report("cleanup", f"rows left for '{TN}' = {left}")
        return left==0
    except Exception as e:
        report("cleanup","ERR "+str(e)[:90]); return False

TARGETS=[("/portal/regions","Filter Regions","regions"),
         ("/portal/administrators","Filter Administrators","administrators"),
         ("/portal/review-questions","Filter Review Questions","review-questions"),
         ("/portal/coverage-type","Filter Coverage Types","coverage-type")]

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH, viewport={"width":1600,"height":1050}, accept_downloads=True).new_page()
    verify_languages_filter(pg)
    out={}
    for route,filt,label in TARGETS:
        try:
            out[label]=verify_create(pg,route,filt,label)
            cleanup(pg,route,filt,label)
        except Exception as e:
            report(label,"ABORT "+str(e)[:110]); out[label]=None
    print("\nCREATE VERDICTS:", json.dumps(out), flush=True)
    b.close()
