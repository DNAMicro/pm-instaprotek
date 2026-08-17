"""SETTINGS - REGISTRATION SURVEY (7). Creates our own survey question first so the
edit / delete scenarios never touch a real one; the question is removed at the end."""
import sys
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

SHEET="SETTINGS - REGISTRATION SURVEY "
Q="RegressionTest0817 survey question?"
Q2="RegressionTest0817 survey question edited?"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:135]}", flush=True)

def rows(pg):
    """Survey questions render as list rows, not .md-table-row."""
    return pg.evaluate("""()=>{
      const out=[];
      document.querySelectorAll('tr, li, .md-list-item, [class*=row]').forEach(e=>{
        const t=(e.innerText||'').replace(/\\s+/g,' ').trim();
        if(t && /edit|delete|menu/.test(t) && t.length<160) out.push(t.slice(0,110));
      });
      return [...new Set(out)];}""")

def find_actions(pg, needle):
    return pg.evaluate(f"""()=>{{
      const els=[...document.querySelectorAll('tr,li,div')].filter(e=>e.textContent.includes({needle!r})&&e.querySelectorAll('button,i.material-icons').length);
      if(!els.length)return null;
      const e=els[els.length-1];
      return {{btns:[...e.querySelectorAll('button,i.material-icons')].map(x=>x.textContent.trim()).slice(0,8),
               cls:(e.className||'').toString().slice(0,50)}};}}""")

def click_action(pg, needle, action):
    return pg.evaluate(f"""()=>{{
      const els=[...document.querySelectorAll('tr,li,div')].filter(e=>e.textContent.includes({needle!r})&&e.querySelectorAll('button,i.material-icons').length);
      if(!els.length)return 'row-not-found';
      const e=els[els.length-1];
      const b=[...e.querySelectorAll('button,i.material-icons')].find(x=>x.textContent.trim()==='{action}');
      if(b){{b.click();return 'clicked';}}
      return 'no-{action}:'+JSON.stringify([...e.querySelectorAll('button,i.material-icons')].map(x=>x.textContent.trim()));}}""")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/survey", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)

    existing=rows(pg)
    body=N.bt(pg)
    listed = "Questions" in body and len(existing)>0
    rec("Grid|1","PASS" if listed else "FAIL",
        f"Created registration survey questions display on the grid — {len(existing)} question row(s) listed, e.g. {existing[:2]}.")

    # create our own question so edit/delete never touch a real one
    N.add_new_grid(pg)
    try:
        pg.locator(".md-dialog:not(.md-dialog--full-page) #question").fill(Q); pg.wait_for_timeout(800)
    except Exception as e: print("   q err", str(e)[:60], flush=True)
    N.sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    made = Q in N.bt(pg)
    print(f"  [setup] own survey question created={made}", flush=True)

    # Grid|2 edit
    info=find_actions(pg, "RegressionTest0817")
    e=click_action(pg,"RegressionTest0817","edit"); pg.wait_for_timeout(5500)
    modal=N.sub_text(pg) or ""
    val=pg.evaluate(f"""()=>{{const d={N.SUB};const i=d&&d.querySelector('#question');return i?i.value:null;}}""")
    rec("Grid|2","PASS" if (e=="clicked" and val) else "FAIL",
        f"Edit ({e}) opens the question record in a modal with its details populated — question field reads '{val}'. Row controls: {info}")

    ok=False
    try:
        L=pg.locator(".md-dialog:not(.md-dialog--full-page) #question")
        L.fill(Q2); pg.wait_for_timeout(800); ok=(L.input_value()==Q2)
    except Exception as ex: print("   upd err", str(ex)[:60], flush=True)
    rec("Grid|3","PASS" if ok else "FAIL", f"The question can be updated — field now reads '{Q2}' ({ok}).")

    sv=N.sub_click(pg,"Save"); pg.wait_for_timeout(7000)
    pg.goto(N.BASE+"/portal/survey", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    saved = Q2 in N.bt(pg)
    rec("Grid|4","PASS" if (not str(sv).startswith('none') and saved) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the change is saved — the edited question is listed on reload ({saved}).")

    d=click_action(pg,"RegressionTest0817","delete"); pg.wait_for_timeout(3500)
    dlg=N.sub_text(pg) or ""
    yn = ("Yes" in dlg and "No" in dlg)
    rec("Grid|5","PASS" if (d=="clicked" and yn) else "FAIL",
        f"Delete shows a confirmation modal with Yes/No ({d}): {dlg[:120].replace(chr(10),' | ')}")

    no_ok=False
    if yn:
        pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
          const d=ds[ds.length-1];const b=[...d.querySelectorAll('button')].find(x=>/No$/.test(x.textContent.trim()));if(b)b.click();}}""")
        pg.wait_for_timeout(4000)
        no_ok = Q2 in N.bt(pg)
    rec("Grid|6","PASS" if no_ok else "FAIL",
        f"Clicking No closes the modal and cancels the delete — the question is still listed ({no_ok}).")

    gone=False
    if yn:
        click_action(pg,"RegressionTest0817","delete"); pg.wait_for_timeout(3500)
        pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
          const d=ds[ds.length-1];const b=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(b)b.click();}}""")
        pg.wait_for_timeout(7000)
        pg.goto(N.BASE+"/portal/survey", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        gone = "RegressionTest0817" not in N.bt(pg)
    rec("Grid|7","PASS" if gone else "FAIL",
        f"Clicking Yes closes the modal and deletes the selected question — removed from the grid ({gone}).")
    print(f"  [teardown] survey question removed={gone}", flush=True)
    b.close()

n,missed,_=resultio.write(SHEET,R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
