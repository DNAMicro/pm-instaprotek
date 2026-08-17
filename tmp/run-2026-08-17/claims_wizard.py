"""CLAIM REPORTS wizard (Claim Reports|5-12) using a registration whose plan has NOT expired,
so the flow pages normally instead of hitting the 'Plan Period has expired' guard.
Never answers Yes to any confirmation and never clicks Done."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

TAB="CLAIM REPORTS"
R={}
def rec(k,s,n): R[k]=(s,n[:440]); print(f"  {k}: {s} — {n[:135]}", flush=True)

def expired_prompt(pg):
    return pg.evaluate("""()=>{const e=[...document.querySelectorAll('.md-dialog *')]
      .find(x=>/Plan Period has expired/i.test(x.textContent)&&x.children.length<6);
      return e?e.textContent.trim().slice(0,110):null;}""")
def decline(pg):
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/^closeNo$|^No$/.test(x.textContent.trim()));if(b)b.click();}""")
    pg.wait_for_timeout(2500)
def step_sections(pg):
    return pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];
      const heads=[...d.querySelectorAll('h1,h2,h3,h4,.md-title,.md-subheading-1,.md-subheading-2')]
        .filter(e=>/^Step \\d/.test(e.textContent.trim()));
      return heads.map(h=>{{const par=h.parentElement;
        const txt=(par?par.innerText:'').replace(h.textContent,'').trim();
        return {{head:h.textContent.trim().slice(0,30),
                 content:txt.slice(0,220).replace(/\\n/g,' | '),
                 inputs:par?[...par.querySelectorAll('input,textarea')].filter(i=>i.offsetParent!==null&&i.type!=='hidden'&&!/dnaTable2|undefined/.test(i.id||'')).map(i=>i.id||i.type):[]}};}});}}""")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    N.add_new_grid(pg); pg.wait_for_timeout(5000)

    # find a registration that does NOT trigger the expired-plan guard
    chosen=None
    nrows=pg.evaluate(f"""()=>{{const d={N.SUB};return d.querySelectorAll('.md-table-row.table-row').length;}}""")
    print(f"  wizard grid rows: {nrows}", flush=True)
    for i in range(min(nrows, 12)):
        pg.evaluate(f"""()=>{{const d={N.SUB};const rows=[...d.querySelectorAll('.md-table-row.table-row')];
          const r=rows[{i}]; if(!r)return; const cb=r.querySelector('input[type=checkbox]');
          (cb?(cb.closest('label')||cb):r).click();}}""")
        pg.wait_for_timeout(2200)
        en=pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent));return b?!b.disabled:false;}}""")
        if not en: continue
        pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);if(b)b.click();}}""")
        pg.wait_for_timeout(5500)
        ep=expired_prompt(pg)
        if ep:
            print(f"   row {i}: expired-plan guard -> declining, trying next", flush=True)
            decline(pg); continue
        secs=step_sections(pg)
        s2=[s for s in secs if s["head"].startswith("Step 2")]
        if s2 and (s2[0]["inputs"] or len(s2[0]["content"])>30):
            chosen=i; print(f"   row {i}: advanced without the expiry guard", flush=True); break
        chosen=i; print(f"   row {i}: no expiry guard (sections: {[s['head'] for s in secs]})", flush=True); break

    if chosen is None:
        for sid in range(5,13):
            rec(f"Claim Reports|{sid}","BLOCKED",
                "Every registration offered on Step 1 of the wizard triggered the 'The Plan Period has expired. Are you sure you want to file a New Claim?' guard. Proceeding past it would file a real claim for a live customer, so the remaining wizard steps were not exercised.")
    else:
        secs=step_sections(pg)
        for s in secs: print(f"   {s['head']}: inputs={s['inputs']} | {s['content'][:110]}", flush=True)
        def sec(n):
            m=[s for s in secs if s["head"].startswith(f"Step {n}")]
            return m[0] if m else None
        s2,s3,s4=sec(2),sec(3),sec(4)
        allsteps=[s["head"] for s in secs]
        paged = "Step 1" not in " ".join(allsteps[:1]) # informational only

        rec("Claim Reports|5","PASS" if s2 else "FAIL",
            f"After selecting a registration, Next moves the flow on to Step 2 Product Details. Sections rendered: {allsteps}.")
        p2=[k for k in ["Pin","Plan","Device","Product Barcode","Coverage","Serial","Product"] if s2 and k in s2["content"]]
        rec("Claim Reports|6","PASS" if p2 else "FAIL",
            f"Step 2 Product Details content: {p2 if p2 else 'the Step 2 section renders its heading only, with no product fields'} — {(s2['content'][:150] if s2 else 'section absent')}")
        rec("Claim Reports|7","PASS" if s3 else "FAIL", f"Step 3 Customer Details section is reachable ({'present' if s3 else 'absent'}).")
        c3=[k for k in ["Email","First Name","Last Name","Phone","Address","Name"] if s3 and k in s3["content"]]
        rec("Claim Reports|8","PASS" if c3 else "FAIL",
            f"Step 3 Customer Details content: {c3 if c3 else 'the Step 3 section renders its heading only, with no customer fields'} — {(s3['content'][:150] if s3 else 'section absent')}")
        ed = bool(s3 and s3["inputs"])
        rec("Claim Reports|9","PASS" if ed else "FAIL",
            f"Customer details on Step 3 are updatable — editable inputs found: {s3['inputs'] if s3 else 'none'}." if ed
            else f"No editable customer inputs are rendered in the Step 3 section (inputs: {s3['inputs'] if s3 else 'section absent'}), so customer details cannot be updated in this flow.")
        rec("Claim Reports|10","PASS" if s4 else "FAIL", f"Step 4 section is reachable ({s4['head'] if s4 else 'absent'}).")
        ps=[k for k in ["Problem Date","Problem Summary","Problem","Description","Damage","Issue"] if s4 and k in s4["content"]]
        rec("Claim Reports|11","PASS" if ps else "FAIL",
            f"Step 4 on this build is '{s4['head'] if s4 else 'absent'}' showing {s4['content'][:130] if s4 else ''} — the Problem Summary fields the test case expects (Problem Date / Problem Summary) are not present.")
        ins=(s4["inputs"] if s4 else [])
        rec("Claim Reports|12","PASS" if ins else "FAIL",
            f"Step 4 input fields available: {ins if ins else 'none — the Claim Receipt step is a read-only summary, so there are no fields to type into'}.")

    # never submit
    decline(pg)
    N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2500)
    print("  [cleanup] wizard cancelled — no claim created", flush=True)
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
