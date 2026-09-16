"""Pass 2: introspect the create forms that failed, fill every required-looking
field, save, and check whether validation feedback is shown. Then re-test the
Grid 10-14 CRUD chain on a record we created ourselves."""
import sys, os, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
TN="VerifyTwo0916"
EV=N.EV+"/verify2"; os.makedirs(EV,exist_ok=True)
def bt(pg): return pg.inner_text("body")
def settle(pg,needle,secs=90):
    for _ in range(int(secs/3)):
        pg.wait_for_timeout(3000)
        if needle in bt(pg): return True
    return False
def controls(pg):
    return pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');if(!d)return[];const o=[];
      d.querySelectorAll('input,textarea,[contenteditable=true]').forEach(e=>{
        if(e.type==='hidden')return;
        const w=e.closest('.md-text-field-container,.md-cell,.Select')||e.parentElement;
        let l='';if(e.id){const q=d.querySelector('label[for="'+e.id+'"]');if(q)l=q.textContent.trim();}
        if(!l&&w)l=(w.innerText||'').split('\\n')[0].trim();
        o.push({id:e.id||null,type:e.type||e.tagName,label:l.slice(0,44),
                sel:!!e.closest('.Select'),vis:e.offsetParent!==null,val:(e.value||'').slice(0,20)});});
      d.querySelectorAll('[id$="-toggle"]').forEach(t=>o.push({id:t.id,type:'md-select',
        label:(t.closest('.md-cell,div')||{}).innerText?.split('\\n')[0]?.trim().slice(0,44)||'',sel:false,vis:true,val:t.textContent.trim().slice(0,20)}));
      return o;}""")
def savebtn(pg):
    return pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');if(!d)return null;
      const b=[...d.querySelectorAll('button')].find(x=>/Save/i.test(x.textContent));
      return b?{text:b.textContent.trim().replace(/\\s+/g,' '),disabled:b.disabled}:null;}""")

def probe(pg, route, filt, label):
    print(f"\n=== {label}: create-form introspection ===", flush=True)
    pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000); settle(pg,filt)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(14000)
    cs=controls(pg)
    for c in cs: print("   CTRL", c, flush=True)
    print("   SAVE:", savebtn(pg), flush=True)
    pg.screenshot(path=EV+f"/{label}_form.png")
    # fill every visible plain text/textarea control
    filled=[]
    for c in cs:
        if not c["vis"] or c["sel"] or not c["id"]: continue
        if c["type"] not in ("text","email","tel","number","TEXTAREA","url"): continue
        try:
            L=pg.locator(f".md-dialog #{c['id']}").first
            v = "qa@test.com" if c["type"]=="email" else ("5551234567" if c["type"]=="tel" else ("1" if c["type"]=="number" else TN))
            L.fill(v, timeout=12000); filled.append(c["id"])
        except Exception as e:
            print(f"   fill-fail {c['id']}: {str(e)[:60]}", flush=True)
    print("   FILLED:", filled, flush=True)
    print("   SAVE after fill:", savebtn(pg), flush=True)
    # click save, then look for validation text
    before=bt(pg)
    try:
        pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
          const b=[...d.querySelectorAll('button')].find(x=>/Save/i.test(x.textContent));if(b&&!b.disabled)b.click();}""")
    except Exception as e: print("   save-click ERR", str(e)[:60], flush=True)
    pg.wait_for_timeout(15000)
    after=bt(pg)
    newlines=[l.strip() for l in after.split("\n") if l.strip() and l.strip() not in before]
    print("   DIALOG OPEN AFTER SAVE:", pg.locator('.md-dialog').count()>0, flush=True)
    print("   NEW TEXT AFTER SAVE:", newlines[:12], flush=True)
    pg.screenshot(path=EV+f"/{label}_aftersave.png")
    pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000); settle(pg,filt)
    try:
        s=pg.locator("input[placeholder*='Search']").first; s.fill(TN); pg.wait_for_timeout(12000)
        n=pg.locator(".md-table-row.table-row").count()
    except Exception: n=-1
    print(f"   VERDICT created={n>0} (rows={n})", flush=True)
    return n>0

def crud(pg, route, filt, label, term):
    """Grid 10-14 against a record matching `term`."""
    print(f"\n=== {label}: CRUD on existing record '{term}' ===", flush=True)
    pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=90000); settle(pg,filt)
    try:
        s=pg.locator("input[placeholder*='Search']").first; s.fill(term); pg.wait_for_timeout(12000)
    except Exception: pass
    rows=pg.locator(".md-table-row.table-row").count()
    print(f"   rows matching '{term}' = {rows}", flush=True)
    if rows==0:
        print("   cannot run CRUD - no row", flush=True); return
    op=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
      if(a){a.click();return 'action';} r.click(); return 'row';}""")
    pg.wait_for_timeout(14000)
    print(f"   open={op} dialog={pg.locator('.md-dialog').count()} fullpage={pg.locator('.md-dialog--full-page').count()}", flush=True)
    print("   CTRLS:", [ (c['id'],c['type'],c['label']) for c in controls(pg)][:8], flush=True)
    print("   SAVE:", savebtn(pg), flush=True)
    pg.screenshot(path=EV+f"/{label}_crud_open.png")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH, viewport={"width":1600,"height":1050}).new_page()
    out={}
    out["regions"]=probe(pg,"/portal/regions","Filter Regions","regions")
    out["review-questions"]=probe(pg,"/portal/review-questions","Filter Review Questions","review-questions")
    crud(pg,"/portal/coverage-type","Filter Coverage Types","coverage-type","Deductible")
    crud(pg,"/portal/languages","Filter Languages","languages","English")
    print("\nPASS2 VERDICTS:", json.dumps(out), flush=True)
    b.close()
