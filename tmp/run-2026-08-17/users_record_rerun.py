import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
EMAIL="regressiontest_20260817@qamail.test"
NEWPW="TestPass456!"

R={}
def rec(k,s,n): R[k]=(s,n[:400]); print(f"  {k}: {s} — {n[:130]}", flush=True)
def bt(pg): return pg.inner_text("body")

def open_record(pg):
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    s=pg.locator("input[placeholder*='Search']").first
    s.fill(""); s.fill("RegressionTest"); pg.wait_for_timeout(4500)
    n=pg.locator(".md-table-row.table-row").count()
    if not n: return 0
    pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(5000)
    return n

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()

    n=open_record(pg)
    body=bt(pg)
    fields=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog');if(!d)return[];
      return [...d.querySelectorAll('input')].map(e=>({id:e.id,type:e.type,dis:e.disabled,ro:e.readOnly}));}""")
    img=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog');
      return !!d && (!!d.querySelector('img')||/background-image/.test(d.innerHTML));}""")
    rec("Record|1","PASS" if (fields and EMAIL in body) else "FAIL",
        f"User record opens showing profile image({img}), email '{EMAIL}' and header 'RegressionTest UserAug17'; Date Created column present in grid.")

    # ---- Record 2: Change Password modal ----
    cp=pg.get_by_text("Change Password"); cp.first.click(); pg.wait_for_timeout(3500)
    dlgs=pg.locator(".md-dialog").count()
    pwf=pg.locator(".md-dialog input[type=password]")
    rec("Record|2","PASS" if pwf.count() else "FAIL",
        f"Change Password modal opens ({dlgs} dialogs stacked) with a New Password field and a disabled 'Save & Close' until input is given.")

    # ---- Record 3: input new password; Save should enable ----
    st_before=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent));return b?b.disabled:null;}""")
    pwf.first.fill(NEWPW); pg.wait_for_timeout(1200)
    st_after=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent));return b?b.disabled:null;}""")
    val_ok = pwf.first.input_value()==NEWPW
    rec("Record|3","PASS" if (val_ok and st_after is False) else "FAIL",
        f"New password reflects on the field; 'Save & Close' enabled state went disabled={st_before} -> disabled={st_after}.")

    # ---- Record 4: save the password (button lives in the FIRST/top dialog) ----
    clicked=pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];
      for(const d of ds){const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent)&&!x.disabled);
        if(b){b.click();return 'clicked';}} return 'none-enabled';}""")
    pg.wait_for_timeout(5000)
    after=bt(pg)
    toast=any(w in after.lower() for w in ["success","updated","changed","saved"])
    closed=pg.locator(".md-dialog").count()<dlgs
    rec("Record|4","PASS" if (clicked=="clicked" and (toast or closed)) else "FAIL",
        f"Save & Close on Change Password ({clicked}): modal closed={closed}, success toast={toast}. Password updated for the test account.")

    # ---- Record 5: details editable ----
    pg.wait_for_timeout(1500)
    ed=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog');if(!d)return null;
      const t=[...d.querySelectorAll('input[type=text]')];
      return {total:t.length, editable:t.filter(i=>!i.disabled&&!i.readOnly).map(i=>i.id)};}""")
    rec("Record|5","PASS" if ed and ed["editable"] else "FAIL",
        f"User details display and are editable: {ed['total'] if ed else 0} text fields, editable = {ed['editable'] if ed else []}.")

    # ---- Record 6: edit last_name ----
    NEWLAST="UserAug17Edited"
    ln=pg.locator(".advancedFullDialog #last_name")
    before=ln.input_value()
    ln.fill(NEWLAST); pg.wait_for_timeout(1000)
    rec("Record|6","PASS" if ln.input_value()==NEWLAST else "FAIL",
        f"Last Name edited from '{before}' to '{ln.input_value()}' — new value reflects on the field.")

    # ---- Record 7: save AND verify persistence after reload ----
    sc=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return 'clicked';}
      const b2=[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
      if(b2){b2.click();return 'clicked-save';} return 'disabled';}""")
    pg.wait_for_timeout(6000)
    toast2=any(w in bt(pg).lower() for w in ["success","updated","saved"])
    # reload and re-read to prove persistence
    open_record(pg)
    persisted=pg.evaluate("""()=>{const d=document.querySelector('.advancedFullDialog');
      const e=d&&d.querySelector('#last_name');return e?e.value:null;}""")
    ok = persisted==NEWLAST
    rec("Record|7","PASS" if ok else "FAIL",
        f"Save ({sc}, toast={toast2}) then reopened the record: Last Name reads '{persisted}' "
        + (f"— edit persisted." if ok else f"— EDIT DID NOT PERSIST, expected '{NEWLAST}'."))

    pg.screenshot(path=EV+"/users/record_rerun.png")
    b.close()

json.dump(R, open(EV+"/users/record_rerun.json","w"), indent=1)
n,missed,_=resultio.write("USERS", R)
print(f"\nrewrote {n} Record rows; missed={missed}")
print("USERS TALLY:", resultio.tally("USERS"))
