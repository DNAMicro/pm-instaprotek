"""PORTAL-REGISTRATION Notes|5-7 + teardown, using the real DOM:
  - record shell   = .md-dialog.md-dialog--full-page
  - sub-modal      = .md-dialog NOT .md-dialog--full-page
  - note row       = .dataTable__notes__row  (actions in .dataTable__notes--actions)
"""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
TAB="PORTAL - REGISTRATION"; REG="112456244808"; TITLE="RegressionTest Note Aug17"
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:135]}", flush=True)

SUB="""(()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('md-dialog--full-page'));
  return ds.length?ds[ds.length-1]:null;})()"""
def sub_text(pg): return pg.evaluate(f"()=>{{const d={SUB};return d?d.innerText:'';}}")
def sub_click(pg,rx):
    return pg.evaluate(f"""()=>{{const d={SUB};if(!d)return 'no-modal';
      const b=[...d.querySelectorAll('button')].find(x=>new RegExp("{rx}","i").test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}
      return 'none:'+JSON.stringify([...d.querySelectorAll('button')].map(x=>x.textContent.trim()));}}""")
def note_action(pg, action):
    return pg.evaluate(f"""()=>{{const row=[...document.querySelectorAll('.dataTable__notes__row')]
        .find(r=>/RegressionTest Note/.test(r.innerText));
      if(!row)return 'row-not-found';
      const acts=row.querySelector('.dataTable__notes--actions')||row;
      const b=[...acts.querySelectorAll('button')].find(x=>x.textContent.trim()==='{action}');
      if(b){{b.click();return 'clicked';}}
      return 'no-{action}:'+JSON.stringify([...acts.querySelectorAll('button')].map(x=>x.textContent.trim()));}}""")

def open_reg(pg):
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
    pg.locator("input[placeholder*='Search']").first.fill(REG); pg.wait_for_timeout(6000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(6500)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    open_reg(pg)
    print("  note present:", TITLE in pg.inner_text("body"), flush=True)

    # ---- Notes|5 ----
    e=note_action(pg,"edit"); pg.wait_for_timeout(6000)
    tv=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return null;const i=d.querySelector('#title');return i?i.value:null;}}""")
    bv=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return null;const x=d.querySelector('[contenteditable=true]');
      return x?x.innerText.trim().slice(0,70):null;}}""")
    rec("Notes|5","PASS" if (e=="clicked" and tv==TITLE) else "FAIL",
        f"Edit ({e}) opens the note modal with existing details populated — Title reads '{tv}', content reads '{bv}'.")

    # ---- Notes|6 ----
    NEW=TITLE+" [edited]"; ok=False
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #title").last
        L.fill(NEW); pg.wait_for_timeout(900); ok=(L.input_value()==NEW)
    except Exception as ex: print("   err",str(ex)[:70], flush=True)
    rec("Notes|6","PASS" if ok else "FAIL", f"Edited title reflects on the field as '{NEW}' ({ok}).")

    # ---- Notes|7 (persistence proven by reload) ----
    sv=sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    open_reg(pg)
    persisted="[edited]" in pg.inner_text("body")
    rec("Notes|7","PASS" if (not str(sv).startswith('none') and persisted) else "FAIL",
        f"Save & Close ('{sv}'); record reopened and the edited note title persists (found={persisted}).")

    # ---- TEARDOWN: delete the note, verifying the dialog before confirming ----
    d=note_action(pg,"delete"); pg.wait_for_timeout(3500)
    dlg=sub_text(pg)
    print(f"  [teardown] delete click={d}; confirm dialog says: {dlg[:160].replace(chr(10),' | ')}", flush=True)
    is_delete_confirm = bool(dlg) and any(w in dlg.lower() for w in ["delete","sure","remove"])
    if is_delete_confirm:
        conf=sub_click(pg,"^Yes$|^Delete$|Confirm")
        pg.wait_for_timeout(6000)
    else:
        conf=f"NOT CONFIRMED — dialog did not read as a delete confirmation: {dlg[:80]!r}"
    open_reg(pg)
    gone = "RegressionTest Note" not in pg.inner_text("body")
    intact=pg.evaluate("""()=>{const b=document.body.innerText;
      return ['Registration Number','Plan','Coverage Amount','Device','Serial Number'].filter(k=>b.includes(k));}""")
    print(f"  [teardown] confirm={conf} | note gone={gone} | registration intact={intact}", flush=True)
    json.dump({"reg":REG,"delete":d,"confirm":conf,"gone":gone,"intact":intact},
              open(EV+"/note_cleanup_final.json","w"), indent=1)
    pg.screenshot(path=EV+"/note_final.png")
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
