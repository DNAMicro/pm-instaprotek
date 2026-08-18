import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:140]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/company", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    found=None
    for i in range(6):
        pg.goto(N.BASE+"/portal/company", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        name=pg.evaluate(f"""()=>{{const rs=[...document.querySelectorAll('.md-table-row.table-row')];
          const r=rs[{i}];return r?r.innerText.split('\\n')[0].trim():null;}}""")
        if not name or "RegressionTest" in name: continue
        pg.evaluate(f"""()=>{{const rs=[...document.querySelectorAll('.md-table-row.table-row')];const r=rs[{i}];
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}}""")
        pg.wait_for_timeout(8000)
        N.click_tab(pg,"Users")
        n=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
        if n>0:
            acts=pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');
              return r?[...r.querySelectorAll('button,i.material-icons')].map(e=>e.textContent.trim()):[];}""")
            found=(name,n,acts); break
    print("  found:", found)
    if found:
        name,n,acts=found
        has=[a for a in acts if 'send' in a.lower() or 'mail' in a.lower() or 'refresh' in a.lower()]
        rec("Users|10","BLOCKED" if has else "FAIL",
            (f"A resend-invite row action IS present on a populated company users grid — company '{name}' with {n} user(s) exposes row actions {acts}. "
             f"Clicking it was NOT executed by choice: it would send an invitation email to a real user on an environment carrying production data."
             if has else
             f"No resend-invite row action is rendered on the users grid. Company '{name}' with {n} user(s) exposes only these row actions: {acts}. The test case expects a resend-invite action on the grid."))
    else:
        rec("Users|10","BLOCKED","Could not find a company with existing users to verify the resend-invite action; the test company has none, and attaching a real user to it would modify live data.")
    b.close()
n,_,_=resultio.write('SETTINGS - COMPANY ',R)
print("tally:",resultio.tally('SETTINGS - COMPANY '))
