"""Search each grid for RegressionTest records and remove them (delete, or deactivate where the
portal offers no hard delete)."""
import sys
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright

TARGETS=[("/portal/user","Users"),("/portal/shop","Repair Shops"),("/portal/affiliate","Affiliates"),
         ("/portal/company","Companies"),("/portal/customer","Customers")]

def confirm(pg):
    txt=N.sub_text(pg) or ""
    if not any(w in txt.lower() for w in ("delete","remove")): return f"no-confirm({txt[:50]!r})"
    return pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
      const d=ds[ds.length-1];if(!d)return 'no-dialog';
      const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));
      if(y){y.click();return 'yes';}return 'no-yes';}""")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    for route,label in TARGETS:
        print(f"\n=== {label} ({route}) ===", flush=True)
        for attempt in range(6):
            pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
            n=N.search_grid(pg,"RegressionTest")
            if n<=0:
                print(f"  no RegressionTest rows remaining", flush=True); break
            row=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
              return r?{txt:r.innerText.replace(/\\s+/g,' ').trim().slice(0,70),
                        acts:[...r.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim())}:null;}""")
            print(f"  row: {row['txt']!r} actions={row['acts']}", flush=True)
            has_delete = any(a=='delete' for a in row["acts"])
            if has_delete:
                pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
                  const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='delete');if(a)a.click();}""")
                pg.wait_for_timeout(3500)
                c=confirm(pg); pg.wait_for_timeout(7000)
                print(f"   delete -> {c}", flush=True)
            else:
                # no hard delete: open the record and set Status = Inactive
                pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
                  const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
                pg.wait_for_timeout(8000)
                st=pg.evaluate("""()=>{const t=document.querySelector('.md-dialog--full-page #status-toggle');return t?t.textContent.trim():null;}""")
                try:
                    o=N.md_open(pg,"status-toggle")
                    if o and any("Inactive" in x for x in o):
                        N.md_pick(pg,"Inactive")
                except Exception as e:
                    print("   status err", str(e)[:60], flush=True)
                pg.wait_for_timeout(1500)
                sv=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
                  const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled);
                  if(b){b.click();return b.textContent.trim();}return 'none';}""")
                pg.wait_for_timeout(8000)
                now=pg.evaluate("""()=>{const e=document.querySelector('.md-dialog--full-page #status');return e?e.value:null;}""")
                print(f"   no hard delete; status {st} -> save({sv}) -> now {now}", flush=True)
                break
    # final state
    print("\n=== FINAL STATE ===", flush=True)
    for route,label in TARGETS:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(7500)
        n=N.search_grid(pg,"RegressionTest")
        rows=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')]
          .map(r=>r.innerText.replace(/\\s+/g,' ').trim().slice(0,70)).filter(t=>/RegressionTest/i.test(t))""")
        print(f"  {label:16s} remaining={len(rows)} {rows}", flush=True)
    b.close()
