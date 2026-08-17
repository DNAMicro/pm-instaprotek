"""BRAND Devices|20-22 (checkbox controls, not radios) + teardown of the test brand and its device."""
import sys
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

SHEET="SETTINGS - BRAND"; TAG="RegressionTest0817"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:135]}", flush=True)

def open_brand(pg):
    pg.goto(N.BASE+"/portal/brand", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    if N.search_grid(pg, TAG)<=0: return False
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8500); return True

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()

    # ---------- Devices|20-22 ----------
    if open_brand(pg):
        N.click_tab(pg,"Devices"); N.add_new_in_record(pg)
        groups=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
          const items=[...d.querySelectorAll('.md-selection-control-container')].map(e=>{{
            const cb=e.querySelector('input[type=checkbox]');
            return {{label:(e.innerText||'').replace(/check_box_outline_blank|check_box/g,'').trim().slice(0,34),
                     checked:cb?cb.checked:null}};}});
          return items;}}""")
        print("  controls:", groups, flush=True)
        default_on=[g["label"] for g in (groups or []) if g["checked"]]
        rec("Devices|20","PASS" if any("IMEI" in x for x in default_on) else "FAIL",
            f"IMEI is the default selected Device ID Type — checked on load: {default_on}; the Device ID Type group offers {[g['label'] for g in (groups or [])][:3]} (rendered as checkboxes, not radio buttons).")
        alt=pg.evaluate(f"""()=>{{const d={N.SUB};
          const items=[...d.querySelectorAll('.md-selection-control-container')];
          const t=items.find(e=>/MEID|Serial/.test(e.innerText));
          if(!t)return null; const cb=t.querySelector('input[type=checkbox]');
          (cb.closest('label')||cb).click();
          return {{label:(t.innerText||'').replace(/check_box_outline_blank|check_box/g,'').trim().slice(0,26), checked:cb.checked}};}}""")
        pg.wait_for_timeout(1500)
        rec("Devices|21","PASS" if (alt and alt.get("checked")) else "FAIL",
            f"Selecting another Device ID type checks it — {alt}.")
        wf=pg.evaluate(f"""()=>{{const d={N.SUB};
          const items=[...d.querySelectorAll('.md-selection-control-container')];
          const t=items.find(e=>/Bypass screen test|Protection not supported/.test(e.innerText));
          if(!t)return null; const cb=t.querySelector('input[type=checkbox]');
          (cb.closest('label')||cb).click();
          return {{label:(t.innerText||'').replace(/check_box_outline_blank|check_box/g,'').trim().slice(0,36), checked:cb.checked}};}}""")
        pg.wait_for_timeout(1500)
        rec("Devices|22","PASS" if (wf and wf.get("checked")) else "FAIL", f"Selecting a workflow option checks it — {wf}.")
        N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2500)
        print("  [cleanup] New Device modal cancelled (no extra device created)", flush=True)

    # ---------- TEARDOWN: delete the device, then the brand ----------
    if open_brand(pg):
        N.click_tab(pg,"Devices")
        for _ in range(3):
            nd=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
            if nd==0: break
            d=pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');if(!r)return 'no-row';
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='delete');
              if(a){a.click();return 'clicked';}return 'no-delete';}""")
            pg.wait_for_timeout(3000)
            txt=N.sub_text(pg) or ""
            if "Yes" in txt:
                pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
                  const d=ds[ds.length-1];const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}}""")
                pg.wait_for_timeout(6000)
            print(f"  [teardown] device delete={d}; dialog said: {txt[:70].replace(chr(10),' | ')}", flush=True)
        # now the brand itself
        d=pg.evaluate("""()=>{const dl=document.querySelector('.md-dialog--full-page');
          const b=[...dl.querySelectorAll('button')].find(x=>/Delete/i.test(x.textContent));
          if(b){b.click();return 'clicked';}return 'no-delete-btn';}""")
        pg.wait_for_timeout(3500)
        txt=N.sub_text(pg) or ""
        print(f"  [teardown] brand delete={d}; confirm: {txt[:110].replace(chr(10),' | ')}", flush=True)
        if "Yes" in txt:
            pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
              const d=ds[ds.length-1];const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}}""")
            pg.wait_for_timeout(7000)
    pg.goto(N.BASE+"/portal/brand", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    left=N.search_grid(pg, TAG)
    print(f"  [teardown] RegressionTest brand rows remaining = {left}", flush=True)
    b.close()

n,missed,_=resultio.write(SHEET,R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
