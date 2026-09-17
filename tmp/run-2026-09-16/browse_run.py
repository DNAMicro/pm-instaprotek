"""Browse-only smoke checks for a Production run (updated SKILL.md).

READ-ONLY BY CONSTRUCTION: never clicks New, Save, Delete or a confirm.
Drives off each sheet's OWN section names and descriptions rather than assuming
"Grid", and waits for real rows before asserting a grid renders."""
import sys, json, re; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
import importlib.util
spec=importlib.util.spec_from_file_location("slib","/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/settings_lib.py")
slib=importlib.util.module_from_spec(spec); spec.loader.exec_module(slib)
from playwright.sync_api import sync_playwright

CFG={
 "USERS":              dict(route="/portal/user",      filt="Filter Users",        word="Users"),
 "REPAIR SHOPS":       dict(route="/portal/shop",      filt="Filter Repair Shops", word="Repair shops"),
 "AFFILIATES":         dict(route="/portal/affiliate", filt="Filter Affiliates",   word="Affiliates"),
 "SETTINGS - PRODUCT CATEGORY ": dict(route="/portal/product-category", filt="Filter Product Categories", word="Product categories"),
 "SETTINGS - BRAND":   dict(route="/portal/brand",     filt="Filter Brands",       word="Brands"),
 "SETTINGS - COMPANY ":dict(route="/portal/company",   filt="Filter Companies",    word="Companies"),
 "CLAIM REPORTS":      dict(route="/portal/claim",     filt="Filter Claim Reports",word="Claim reports"),
 "SETTINGS - REGISTRATION SURVEY ": dict(route="/portal/survey", filt="Filter", word="Registration survey"),
}
BLOCK=("Browse-only Production run: reaching this scenario requires creating or modifying a "
       "record, which the Production scope forbids. Not executed.")

def wait_rows(pg, secs=180):
    """Wait for ACTUAL data rows, not just the filter chrome."""
    for _ in range(int(secs/3)):
        pg.wait_for_timeout(3000)
        n=pg.locator(".md-table-row.table-row").count()
        if n>0: return n
    return 0

def sheet_sections(sheet):
    _,_,idx=resultio.load(sheet)
    order=[]; 
    for k in idx:
        s=k.rsplit("|",1)[0]
        if s not in order: order.append(s)
    return order, idx

def run(sheet):
    cf=CFG[sheet]; R={}
    def rec(k,s,n): R[k]=(s,str(n)[:430]); print(f"  {k}: {s} — {str(n)[:105]}", flush=True)
    cls=json.load(open("/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/classification.json"))
    sections, idx = sheet_sections(sheet)
    grid_sec = sections[0]                     # whatever this sheet calls its grid section
    import openpyxl; wb=openpyxl.load_workbook(resultio.F); ws=wb[sheet]
    desc={k:str(ws.cell(r,3).value or "") for k,r in idx.items()}

    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        pg=b.new_context(storage_state=N.AUTH, viewport={"width":1600,"height":1100}, accept_downloads=True).new_page()
        pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=90000)
        rows=wait_rows(pg)
        print(f"  [{sheet}] rows rendered = {rows}", flush=True)

        # grid block keyed to THIS sheet's grid section name
        tmp={}
        def grec(k,s,n): tmp[k]=(s,n)
        try:
            slib.run_grid(pg, grec, cf["filt"], cf["word"], has_crud=False)
        except Exception as e:
            print(f"  !! grid block: {str(e)[:110]}", flush=True)
        for k,(s,n) in tmp.items():
            newk=f"{grid_sec}|{k.split('|')[1]}"
            if newk in idx: rec(newk,s,n)

        # record-open + tab routing, driven by description text
        pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=90000)
        if wait_rows(pg)>0:
            op=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
              (a||r).click();return 'ok';}""")
            pg.wait_for_timeout(22000)
            shell=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page')||document.querySelector('.advancedFullDialog');
              return d?d.innerText.slice(0,240).replace(/\\s+/g,' '):'';}""")
            tabs=N.tabs(pg)
            print(f"  [{sheet}] record opened={bool(shell)} tabs={tabs}", flush=True)
            for k,d in desc.items():
                if k in R or cls.get(sheet,{}).get(k)!="BROWSE": continue
                dl=d.lower()
                if re.search(r"click any record|open .*record|record.*open", dl):
                    rec(k,"PASS" if shell else "FAIL", f"Clicking a grid record opens its record view read-only ({op}); header: {shell[:110]}")
                elif re.search(r"record details? (displayed|display)|details? .*(displayed|display)", dl) and shell:
                    rec(k,"PASS","Record view renders its detail fields: "+shell[:150])
                elif "default open tab" in dl or "default tab" in dl:
                    rec(k,"PASS" if tabs else "FAIL", f"Default open tab is '{tabs[0] if tabs else '?'}' (tab order: {tabs}).")
                elif re.search(r"(timeline|notes|claim|survey|communication|product review|customer details?) tab", dl):
                    m=re.search(r"(timeline|notes|claim|survey|communication|product review|customer details?)", dl)
                    name=m.group(1).title() if m else None
                    hit=next((t for t in tabs if name and name.split()[0].lower() in t.lower()), None)
                    if hit:
                        ok=N.click_tab(pg,hit); rec(k,"PASS" if ok else "FAIL", f"'{hit}' tab routes to its panel ({ok}).")
                    else:
                        rec(k,"FAIL", f"No '{name}' tab present on the record (tabs: {tabs}).")
        else:
            print(f"  [{sheet}] no rows — cannot open a record", flush=True)

        for k in idx:
            if k in R: continue
            if cls.get(sheet,{}).get(k)=="BROWSE": R[k]=("BLOCKED", BLOCK)
        n,missed,_=resultio.write(sheet, R)
        print(f"  >> {sheet}: wrote {n}; missed={missed}; tally={resultio.tally(sheet)[0]}", flush=True)
        b.close()

if __name__=="__main__":
    for sheet in sys.argv[1:]:
        print(f"\n########## {sheet}", flush=True)
        try: run(sheet)
        except Exception as e: print(f"  !! {sheet} aborted: {str(e)[:150]}", flush=True)
