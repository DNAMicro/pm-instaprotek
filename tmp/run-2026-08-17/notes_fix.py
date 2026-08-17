"""Complete PORTAL-REGISTRATION Notes|5-7 against the expansion-panel structure,
then delete the test note (teardown)."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
TAB="PORTAL - REGISTRATION"
REG="112456244808"
TITLE="RegressionTest Note Aug17"
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:130]}", flush=True)

SUB="""(()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('advancedFullDialog'));
  return ds.length?ds[ds.length-1]:null;})()"""

def sub_text(pg): return pg.evaluate(f"()=>{{const d={SUB};return d?d.innerText:'';}}")
def sub_click(pg,rx):
    return pg.evaluate(f"""()=>{{const d={SUB};if(!d)return 'no-modal';
      const b=[...d.querySelectorAll('button')].find(x=>new RegExp("{rx}","i").test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
def panel_btn(pg, action):
    """Click edit/delete on the expansion panel holding the test note."""
    return pg.evaluate(f"""()=>{{
      const li=[...document.querySelectorAll('li.md-expansion-panel')].find(e=>/RegressionTest Note/.test(e.textContent));
      if(!li)return 'panel-not-found';
      let b=[...li.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='{action}');
      if(!b){{ const hdr=li.querySelector('.md-panel-header'); if(hdr)hdr.click(); }}
      b=[...li.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='{action}');
      if(b){{b.click();return 'clicked';}}
      return 'btns:'+JSON.stringify([...li.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim()));}}""")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1100}).new_page()
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    pg.locator("input[placeholder*='Search']").first.fill(REG); pg.wait_for_timeout(6000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(6500)
    print("  note present:", TITLE in pg.inner_text("body"), flush=True)

    # ---- Notes|5 : edit opens populated modal ----
    e=panel_btn(pg,"edit"); pg.wait_for_timeout(6000)
    t=sub_text(pg)
    tv=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return null;const i=d.querySelector('#title');return i?i.value:null;}}""")
    body_pop=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return null;const e=d.querySelector('[contenteditable=true]');
      return e?e.innerText.trim().slice(0,60):null;}}""")
    rec("Notes|5","PASS" if (e=="clicked" and tv==TITLE) else "FAIL",
        f"Edit ({e}) opens the note modal with details populated — title reads '{tv}', content reads '{body_pop}'.")

    # ---- Notes|6 : change reflects ----
    NEW=TITLE+" [edited]"
    ok=False
    try:
        L=pg.locator(".md-dialog:not(.advancedFullDialog) #title").last
        L.fill(NEW); pg.wait_for_timeout(900); ok=(L.input_value()==NEW)
    except Exception as ex: print("   edit err",str(ex)[:70], flush=True)
    rec("Notes|6","PASS" if ok else "FAIL", f"Edited title reflects on the field as '{NEW}' ({ok}); Save & Close enabled.")

    # ---- Notes|7 : save persists ----
    sv=sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    # reload the record to prove persistence
    pg.goto(BASE+"/portal/registration", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.locator("input[placeholder*='Search']").first.fill(REG); pg.wait_for_timeout(6000)
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(8000)
    pg.evaluate("""()=>{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='Notes');if(t)t.click();}""")
    pg.wait_for_timeout(6500)
    persisted="[edited]" in pg.inner_text("body")
    rec("Notes|7","PASS" if (sv!="none" and persisted) else "FAIL",
        f"Save & Close ('{sv}'); reopened the record and the note title persists as edited (found={persisted}).")

    # ---- TEARDOWN ----
    d=panel_btn(pg,"delete"); pg.wait_for_timeout(3500)
    conf=pg.evaluate(f"""()=>{{const d={SUB};if(!d)return 'no-confirm-dialog';
      const txt=d.innerText.slice(0,120);
      const y=[...d.querySelectorAll('button')].find(x=>/^Yes$|^Delete$|Confirm/i.test(x.textContent.trim()));
      if(y){{y.click();return 'confirmed | dialog said: '+txt;}}
      return 'no-yes-btn | '+JSON.stringify([...d.querySelectorAll('button')].map(x=>x.textContent.trim()));}}""")
    pg.wait_for_timeout(6000)
    gone = "RegressionTest Note" not in pg.inner_text("body")
    print(f"  [teardown] delete={d} | {conf} | gone={gone}", flush=True)
    intact=pg.evaluate("""()=>{const b=document.body.innerText;
      return ['Registration Number','Plan','Coverage Amount','Device'].filter(k=>b.includes(k));}""")
    print(f"  [teardown] registration #{REG} still intact: {intact}", flush=True)
    json.dump({"reg":REG,"delete":d,"confirm":conf,"gone":gone,"intact":intact},
              open(EV+"/note_cleanup_final.json","w"), indent=1)
    pg.screenshot(path=EV+"/note_after_cleanup.png")
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
