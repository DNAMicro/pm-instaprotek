import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S
from playwright.sync_api import sync_playwright
SHEET="SETTINGS - REGIONS"
R={}
def rec(k,s,n): R[k]=(s,n[:440]); print(f"  {k}: {s} — {n[:130]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/regions", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    existing=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')].map(r=>r.innerText.split('\\n')[0].trim())""")
    NOTE=(f"The Region Name field is a dropdown of selectable regions, not a free-text field, and it offers NO options: "
          f"the four selectable regions (Canada, Puerto Rico, United Kingdom, United States) all already exist as records {existing}. "
          f"A new region therefore cannot be created on this environment.")
    rec("New Region|4","BLOCKED", NOTE+" Typing into the field does not set a value and Save is rejected with 'Region Name is required'.")
    rec("New Region|5","BLOCKED", "Cannot save a new region — no selectable region value is available (see New Region|4).")
    # Grid|10 read-only on a real region
    opened=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();return 'ok';}""")
    pg.wait_for_timeout(6000)
    t=N.sub_text(pg) or ""
    rec("Grid|10","PASS" if (opened=="ok" and t) else "FAIL",
        f"Clicking a record on the regions grid opens its record modal: {t[:120].replace(chr(10),' | ')}")
    for sid,what in [(11,"Editing the region name"),(12,"Saving an edited region"),(13,"Deleting a region"),(14,"Confirming the delete")]:
        rec(f"Grid|{sid}","BLOCKED",
            f"{what} was not executed: only the four live production region records exist (no self-created test record is possible — see New Region|4), and regions are live configuration data on an environment carrying production traffic.")
    b.close()
n,missed,_=resultio.write(SHEET,R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
