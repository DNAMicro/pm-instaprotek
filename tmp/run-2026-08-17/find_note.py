"""Locate and delete the RegressionTest note left on a registration during reg_run3."""
import sys, json
from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
NEEDLE="RegressionTest Note"

def dismiss_nav(pg):
    for _ in range(3):
        t=pg.evaluate("""()=>{const d=[...document.querySelectorAll('.md-dialog')].find(x=>/unsaved changes|Confirm Navigation/i.test(x.innerText));
          if(!d)return null;const b=[...d.querySelectorAll('button')].find(x=>/Leave|Yes|Confirm|OK/i.test(x.textContent));
          if(b){b.click();return 'left';}return 'stuck';}""")
        if t is None: return
        pg.wait_for_timeout(1200)

found=None
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    for i in range(0,30):
        pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(2500); dismiss_nav(pg); pg.wait_for_timeout(6500)
        n=pg.locator(".md-table-row.table-row").count()
        if i>=n: print(f"  row {i} beyond grid ({n})"); break
        ok=pg.evaluate(f"""()=>{{const rows=[...document.querySelectorAll('.md-table-row.table-row')];
          const r=rows[{i}]; if(!r)return false;
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));
          (a||r).click(); return true;}}""")
        if not ok: break
        pg.wait_for_timeout(7000)
        reg=pg.evaluate("""()=>{const m=document.body.innerText.match(/Registration:\\s*(\\d+)/);return m?m[1]:null;}""")
        pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
        pg.wait_for_timeout(5500)
        has=NEEDLE in pg.inner_text("body")
        print(f"  row {i:2d} reg #{reg} notes-hit={has}", flush=True)
        if has:
            found=reg
            # delete it
            d=pg.evaluate("""()=>{const rows=[...document.querySelectorAll('.md-table-row.table-row')];
              for(const r of rows){ if(/RegressionTest Note/.test(r.innerText)){
                const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete/.test(e.textContent));
                if(a){a.click();return 'clicked';} return 'row-no-delete-btn';}}
              return 'row-not-located';}""")
            pg.wait_for_timeout(3500)
            conf=pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];const d=ds[ds.length-1];
              if(!d)return 'no-dialog';
              const y=[...d.querySelectorAll('button')].find(x=>/^Yes$|^Delete$|Confirm/i.test(x.textContent.trim()));
              if(y){y.click();return 'confirmed';}
              return 'btns:'+JSON.stringify([...d.querySelectorAll('button')].map(x=>x.textContent.trim()).slice(-5));}""")
            pg.wait_for_timeout(6000)
            gone = NEEDLE not in pg.inner_text("body")
            print(f"  >>> delete={d} confirm={conf} gone={gone}", flush=True)
            json.dump({"reg":reg,"delete":d,"confirm":conf,"gone":gone}, open(EV+"/note_cleanup_final.json","w"), indent=1)
            if gone: break
    b.close()
print("FOUND ON:", found)
