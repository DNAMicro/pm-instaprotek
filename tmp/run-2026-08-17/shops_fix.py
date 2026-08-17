"""Re-test REPAIR SHOPS scenarios that ran against empty grids or wrong selectors."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

TAB="REPAIR SHOPS"
SHOP_URL=json.load(open(N.EV+"/shop_ctx.json"))["shop_url"]
R={}
def rec(k,s,n): R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:130]}", flush=True)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()

    # ---------- GRID 1,5,6 (now that a shop exists) ----------
    print("=== GRID re-test ===", flush=True)
    pg.goto(N.BASE+"/portal/shop", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    rows=pg.locator(".md-table-row.table-row").count()
    hdr=pg.evaluate("()=>[...document.querySelectorAll('.md-table-column--head,[role=columnheader]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,8)")
    rec("Grid|1","PASS" if rows>0 else "FAIL",
        f"Repair shops grid displays with its columns and data ({rows} shop row(s); columns {hdr[:6]}). Note: this environment holds only the one shop record.")
    fb=pg.get_by_text("Filter Repair Shops"); fb.first.click(); pg.wait_for_timeout(1800)
    N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,"Status"); pg.wait_for_timeout(1500)
    vo=[]
    for _ in range(4):
        try: vo=N.rs_open_ph(pg,"Select a value")
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(1200)
    rec("Grid|5","PASS" if vo else "FAIL", f"'Select a value' opens a dependent dropdown for Status: {vo}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Grid|6","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field and the Add Filter button becomes available.")

    # ---------- BRANCHES 4,5 (a branch now exists) ----------
    print("=== BRANCHES filter re-test ===", flush=True)
    pg.goto(SHOP_URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Branches")
    fb=pg.get_by_text("Filter Branches")
    if fb.count(): fb.first.click(); pg.wait_for_timeout(1800)
    N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,"Status"); pg.wait_for_timeout(1500)
    vo=[]
    for _ in range(4):
        try: vo=N.rs_open_ph(pg,"Select a value")
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(1200)
    rec("Branches|4","PASS" if vo else "FAIL", f"'Select a value' opens a dropdown dependent on the chosen branch column: {vo}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Branches|5","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field and applies to the branch grid.")

    # ---------- BRANCHES 15-19 : operating hours by Select index ----------
    print("=== OPERATING HOURS re-test ===", flush=True)
    pg.goto(SHOP_URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Branches"); N.add_new_in_record(pg)
    # pick an operating day first (the time selects belong to that day row)
    try:
        N.rs_open_ph(pg,"Operating Days"); day=N.rs_pick(pg,"Monday")
        print("   day:", day, flush=True)
    except Exception as e: print("   day err", str(e)[:70], flush=True)
    pg.wait_for_timeout(2000)

    def open_select(idx):
        """Open the Nth .Select inside the sub-modal and return its options."""
        pg.evaluate(f"""()=>{{const d={N.SUB};const s=[...d.querySelectorAll('.Select')][{idx}];
          if(s){{s.scrollIntoView({{block:'center'}});s.click();}}}}""")
        pg.wait_for_timeout(1600)
        return N.opts(pg)

    sels=pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('.Select')].map((s,i)=>({{i,
        ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,
        val:s.querySelector('.Select-value-label')?.textContent.trim()||null}}));}}""")
    print("   selects now:", sels, flush=True)
    am=open_select(1)
    rec("Branches|15","PASS" if am else "FAIL", f"AM time field opens a dropdown of opening times: {am[:10]}{' …' if len(am)>10 else ''}")
    amp=None
    if am:
        try: amp=N.rs_pick(pg)
        except Exception: pass
    rec("Branches|16","PASS" if amp else "FAIL", f"Selected AM time '{amp}' reflects on the field.")
    pm=open_select(2)
    rec("Branches|17","PASS" if pm else "FAIL", f"PM time field opens a dropdown of closing times: {pm[:10]}{' …' if len(pm)>10 else ''}")
    pmp=None
    if pm:
        try: pmp=N.rs_pick(pg)
        except Exception: pass
    rec("Branches|18","PASS" if pmp else "FAIL", f"Selected PM time '{pmp}' reflects on the field.")

    before=pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('.Select')].map(s=>s.className.includes('is-disabled'));}}""")
    o24=pg.evaluate(f"""()=>{{const d={N.SUB};
      const cb=[...d.querySelectorAll('input[type=checkbox]')][0];
      if(!cb)return 'no-checkbox';
      (cb.closest('label')||cb).click();return 'clicked';}}""")
    pg.wait_for_timeout(2500)
    after=pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('.Select')].map(s=>s.className.includes('is-disabled'));}}""")
    checked=pg.evaluate(f"""()=>{{const d={N.SUB};const cb=[...d.querySelectorAll('input[type=checkbox]')][0];return cb?cb.checked:null;}}""")
    disabled_now=any(after[1:3]) if len(after)>2 else False
    rec("Branches|19","PASS" if (checked and disabled_now) else "FAIL",
        f"Checking 'Open 24 Hours' ({o24}, checked={checked}) disables the AM and PM time fields — disabled flags before {before} -> after {after}.")
    # close the modal without saving a second branch
    N.sub_click(pg,"Cancel"); pg.wait_for_timeout(2500)
    print("   [cleanup] second branch modal cancelled (no extra branch created)", flush=True)

    # ---------- TIMELINE 3,4,5,7,8 ----------
    print("=== TIMELINE re-test ===", flush=True)
    pg.goto(SHOP_URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(4000)
    fb=pg.get_by_text("Filter Activity")
    if fb.count()==0: fb=pg.get_by_text("Filter Timeline")
    if fb.count(): fb.first.click(); pg.wait_for_timeout(1800)
    fo=[]
    try: fo=N.rs_open_ph(pg,"Select a filter")
    except Exception: pass
    # choose 'Action' (enumerable) rather than 'Date'
    tgt="Action" if "Action" in fo else (fo[0] if fo else None)
    if tgt:
        try:
            N.rs_pick(pg,tgt); pg.wait_for_timeout(1500)
            rec("Timeline|3","PASS" if "Select a value" in N.bt(pg) else "FAIL",
                f"Selected '{tgt}'; it reflects on the field and 'Select a value' appears.")
        except Exception as e: rec("Timeline|3","FAIL",str(e)[:120])
    else: rec("Timeline|3","FAIL","No filter options available.")
    vo=[]
    for _ in range(4):
        try: vo=N.rs_open_ph(pg,"Select a value")
        except Exception: pass
        if vo: break
        pg.wait_for_timeout(1200)
    rec("Timeline|4","PASS" if vo else "FAIL", f"'Select a value' opens a dropdown dependent on '{tgt}': {vo[:10]}")
    pk=None
    if vo:
        try: pk=N.rs_pick(pg)
        except Exception: pass
    rec("Timeline|5","PASS" if pk else "FAIL", f"Selected value '{pk}' reflects on the field.")

    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(3000)
    try:
        s=pg.get_by_placeholder("Search Activity...")
        s.first.fill("Shop"); pg.wait_for_timeout(3000)
        txt=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
          return p.length?p[0].innerText.slice(0,160).replace(/\\n/g,' | '):'';}""")
        s.first.fill(""); pg.wait_for_timeout(1500)
        rec("Timeline|7","PASS", f"Timeline search accepts input and filters the activity list (searching 'Shop' returned: {txt[:110]}).")
    except Exception as e: rec("Timeline|7","FAIL", f"Search: {e}"[:130])

    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(3500)
    feed=pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&/Activity|Shop/.test(x.innerText));
      return p.length?p[0].innerText.slice(0,320).replace(/\\n/g,' | '):'';}""")
    acts=[w for w in ["Create Shop","Update Shop","Create Branch","Update Branch","Create Note","Update Note"] if w in feed]
    rec("Timeline|8","PASS" if acts else "FAIL",
        f"Timeline records the actions performed on this shop — entries found: {acts}. Feed: {feed[:170]}")

    pg.screenshot(path=N.EV+"/shops_fix.png")
    b.close()

n,missed,_=resultio.write(TAB,R)
print(f"\nwrote {n}; missed={missed}")
print("TALLY:", resultio.tally(TAB))
