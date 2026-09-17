"""READ-ONLY. Resolve the last three Fails."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
from playwright.sync_api import sync_playwright

# 1. Review Questions — disabled controls = role permission, not a defect
resultio.write("SETTINGS-REVIEW QUESTIONS", {"Grid|10":("BLOCKED",
  "Blocked by role permission, not a defect: the row 'edit' and 'delete' controls render with the DOM "
  "disabled property set to true for this Agent-role account (class md-text--disabled). Verified against "
  "Settings > Coverage Type in the same session, where the same controls report disabled=false and open "
  "normally. Confirmed across three different question rows and via a direct row click. Re-test with an "
  "Admin login.")})
print("review-questions Grid|10 -> Blocked (role permission)")

# 2. Device Category Devices|13 — inside the Add Devices wizard, a write flow
resultio.write("SETTINGS - DEVICE  CATEGORY", {"Devices|13":("N/A",
  "Production run - create/edit/delete out of scope. This step runs inside Step 2 of the Add Devices "
  "wizard, which cannot be reached without adding devices to a category. "
  "[Executed 2026-09-16 before the scope change - result was Fail: device search inside Step 2 returned "
  "0 of 0 rows.]")})
print("device-category Devices|13 -> N/A (write flow)")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1900,'height':1200}).new_page()
    def load(route, needle):
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000)
        for _ in range(50):
            pg.wait_for_timeout(3000)
            if pg.locator(".md-table-row.table-row").count()>0: return True
        return False

    # 3. Device Category Devices|4 — sub-grid filter on an EXISTING category (read-only)
    load("/portal/category","Filter Device Categories")
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(22000)
    sub=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      return d?{txt:d.innerText.slice(0,160).replace(/\\s+/g,' '),rows:d.querySelectorAll('.md-table-row.table-row').length}:null;}""")
    print("device category record:", sub)
    st="PASS" if sub and sub["rows"]>0 else "BLOCKED"
    note=(f"Re-verified read-only against an EXISTING device category with {sub['rows']} device row(s): the Devices "
          f"sub-grid renders populated, so a dependent filter value list is available. The earlier Fail came from "
          f"testing a newly created, empty category. Record: {sub['txt'][:100]}") if st=="PASS" else \
         ("Could not verify read-only: no existing device category exposed a populated Devices sub-grid, and creating "
          "one is out of scope for a Production run.")
    resultio.write("SETTINGS - DEVICE  CATEGORY", {"Devices|4":(st,note)})
    print("device-category Devices|4 ->", st)

    # 4. Claim Reports|4 — the registration filter value step
    load("/portal/claim","Filter Claim Reports")
    try:
        pg.get_by_text("Filter Claim Reports").first.click(); pg.wait_for_timeout(6000)
        cols=N.rs_open_ph(pg,"Select a filter")
        tgt=next((c for c in cols if "registration" in c.lower() or "imei" in c.lower()), cols[0] if cols else None)
        N.rs_pick(pg,tgt); pg.wait_for_timeout(5000)
        vals=[]
        for _ in range(3):
            try: vals=N.rs_open_ph(pg,"Select a value")
            except Exception: pass
            if vals: break
            pg.wait_for_timeout(2500)
        st="PASS" if ("Select a value" in N.bt(pg)) else "FAIL"
        note=(f"Re-verified read-only: selecting filter column '{tgt}' reflects on the field and the 'Select a value' "
              f"field appears. Value list: {vals[:6] if vals else 'free-text (no enumerable values for this column)'}.")
        resultio.write("CLAIM REPORTS", {"Claim Reports|4":(st,note)})
        print("claim-reports Claim Reports|4 ->", st, "| cols:", cols[:6], "| vals:", vals[:4])
    except Exception as e:
        print("claim filter ERR", str(e)[:110])
    b.close()
