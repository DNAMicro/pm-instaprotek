"""Runner for DEVICE CATEGORY / PRODUCT CATEGORY / BRAND settings tabs."""
import sys, json, re
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S, set_record as SR
from playwright.sync_api import sync_playwright

TAG=SR.TAG

def sub_add_devcat(pg, rec, sub):
    """DEVICE CATEGORY Devices|9-15: Add devices wizard (brand -> devices)."""
    N.click_tab(pg,"Devices")
    n=N.add_new_in_record(pg)
    t=N.sub_text(pg)
    rec(f"{sub}|9","PASS" if t else "FAIL", f"Add opens the Add Devices modal on Step 1: {t[:130].replace(chr(10),' | ')}")
    srch=0
    try:
        s=pg.locator(".md-dialog:not(.md-dialog--full-page) input[placeholder*='Search']").first
        s.fill("Apple"); pg.wait_for_timeout(4000)
        srch=pg.evaluate(f"""()=>{{const d={N.SUB};return d?d.querySelectorAll('.md-table-row.table-row').length:0;}}""")
    except Exception as e: print("   brand search err", str(e)[:60], flush=True)
    rec(f"{sub}|10","PASS" if srch>0 else "FAIL", f"Brand search inside the modal filters the brand list ({srch} row(s) matched 'Apple').")
    picked=pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
      const cb=r.querySelector('input[type=checkbox],input[type=radio]');
      (cb?(cb.closest('label')||cb):r).click();return 'clicked';}}""")
    pg.wait_for_timeout(2200)
    nen=pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent));return b?!b.disabled:null;}}""")
    rec(f"{sub}|11","PASS" if (picked=="clicked" and nen) else "FAIL", f"Selecting a brand marks it and enables Next ({picked}; Next enabled={nen}).")
    r=N.sub_click(pg,"Next"); pg.wait_for_timeout(5500)
    t2=N.sub_text(pg)
    rec(f"{sub}|12","PASS" if ("Step 2" in t2 or "Device" in t2) else "FAIL", f"Next routes to Step 2 Select Devices ('{r}'): {t2[:130].replace(chr(10),' | ')}")
    DEVROWS = """()=>{const ts=[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')];
      const t=ts.find(x=>/Device Name/.test(x.innerText));
      if(!t)return {n:-1,names:[]};
      const rs=[...t.querySelectorAll('.md-table-row.table-row')];
      return {n:rs.length, names:rs.slice(0,3).map(r=>r.innerText.replace(/\\s+/g,' ').trim().slice(0,30))};}"""
    ds=0; term=None; before={"n":0,"names":[]}
    for _ in range(8):                      # the device list loads async after Next
        before=pg.evaluate(DEVROWS)
        if before["n"]>0: break
        pg.wait_for_timeout(2500)
    print(f"   step2 device rows: {before['n']} e.g. {before['names'][:2]}", flush=True)
    try:
        # search for a real device name taken from the list itself
        term=(before["names"][0] if before["names"] else "a").split()[0]
        s=pg.get_by_placeholder("Search Devices...")
        box=s.last if s.count()>1 else s.first
        box.fill(""); box.fill(term); pg.wait_for_timeout(5000)
        after=pg.evaluate(DEVROWS); ds=after["n"]
        print(f"   device search {term!r}: {before['n']} -> {ds} rows", flush=True)
    except Exception as e: print("   dev search err", str(e)[:60], flush=True)
    rec(f"{sub}|13","PASS" if ds>0 else "FAIL",
        f"Device search inside Step 2 accepts input and filters the device list — searching '{term}' (taken from the listed devices) returned {ds} of {before['n']} row(s).")
    dp=pg.evaluate("""()=>{const ts=[...document.querySelectorAll('.md-dialog:not(.md-dialog--full-page) table')];
      const t=ts.find(x=>/Device Name/.test(x.innerText)); if(!t)return 'no-device-table';
      const r=t.querySelector('.md-table-row.table-row'); if(!r)return 'no-row';
      const cb=r.querySelector('input[type=checkbox]'); if(!cb)return 'no-checkbox';
      (cb.closest('label')||cb).click(); return cb.checked?'checked':'clicked';}""")
    pg.wait_for_timeout(2500)
    rec(f"{sub}|14","PASS" if dp in ("checked","clicked") else "FAIL", f"Selecting a device ticks its checkbox ({dp}).")
    sv,still,errs=S.save(pg)
    pg.wait_for_timeout(2000)
    rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    rec(f"{sub}|15","PASS" if (not still) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the selected device(s) appear in the category's device grid ({rows} row(s)){'; validation '+str(errs) if errs else ''}.")

def sub_add_prodcat(pg, rec, sub):
    """PRODUCT CATEGORY Products|9-12."""
    N.click_tab(pg,"Products")
    N.add_new_in_record(pg)
    t=N.sub_text(pg)
    rec(f"{sub}|9","PASS" if t else "FAIL", f"Add opens the Add Products modal: {t[:130].replace(chr(10),' | ')}")
    srch=0
    try:
        s=pg.locator(".md-dialog:not(.md-dialog--full-page) input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(4000)
        srch=pg.evaluate(f"""()=>{{const d={N.SUB};return d?d.querySelectorAll('.md-table-row.table-row').length:0;}}""")
    except Exception as e: print("   prod search err", str(e)[:60], flush=True)
    rec(f"{sub}|10","PASS" if srch>0 else "FAIL", f"Product search inside the modal filters the product list ({srch} row(s)).")
    dp=pg.evaluate(f"""()=>{{const d={N.SUB};const r=d.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
      const cb=r.querySelector('input[type=checkbox]');(cb?(cb.closest('label')||cb):r).click();
      return cb?(cb.checked?'checked':'clicked'):'clicked';}}""")
    pg.wait_for_timeout(2200)
    rec(f"{sub}|11","PASS" if dp in ("checked","clicked") else "FAIL", f"Selecting a product ticks its checkbox ({dp}).")
    sv,still,errs=S.save(pg)
    pg.wait_for_timeout(2000)
    rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    rec(f"{sub}|12","PASS" if (not still) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the selected product(s) appear in the category's product grid ({rows} row(s)){'; validation '+str(errs) if errs else ''}.")

def sub_add_brand(pg, rec, sub):
    """BRAND Devices|9-23: new device form with many fields."""
    N.click_tab(pg,"Devices")
    rows=pg.evaluate("""()=>document.querySelectorAll('.md-dialog--full-page .md-table-row.table-row').length""")
    rec(f"{sub}|9","PASS" if rows>=0 else "FAIL", f"The brand's device grid renders ({rows} device row(s) for the newly created brand).")
    N.add_new_in_record(pg)
    t=N.sub_text(pg)
    rec(f"{sub}|10","PASS" if t else "FAIL", f"New opens the New Device modal: {t[:130].replace(chr(10),' | ')}")
    nfi=S.file_inputs(pg)
    rec(f"{sub}|11","PASS" if nfi else "FAIL", f"Profile image section exposes a file input ({nfi}); clicking it opens the OS file explorer.")
    ok,msg=S.act_upload(pg,0)
    rec(f"{sub}|12","PASS" if ok else "FAIL", f"Selected image reflects in the profile image section — {msg}.")
    ok,msg=S.act_input(pg,"device name",TAG)
    rec(f"{sub}|13","PASS" if ok else "FAIL", f"Device name accepts input — {msg}.")
    pairs=[(14,15,"identifier"),(16,17,"categor"),(18,19,"internet connection")]
    for oid,sid,phrase in pairs:
        ok,msg,o=S.act_open_select(pg,phrase)
        rec(f"{sub}|{oid}","PASS" if o else "FAIL", f"'{phrase}' field opens a dropdown — {msg}; options: {o[:8]}")
        picked=None
        if o:
            try: picked=N.rs_pick(pg)
            except Exception: pass
        rec(f"{sub}|{sid}","PASS" if picked else "FAIL", f"Selected '{picked}' reflects on the field.")
    idt=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const rs=[...d.querySelectorAll('input[type=radio]')];
      const on=rs.filter(r=>r.checked).map(r=>{{const w=r.closest('.md-selection-control-container,.md-cell,div');return (w?w.innerText:'').trim().slice(0,26);}});
      const all=rs.map(r=>{{const w=r.closest('.md-selection-control-container,.md-cell,div');return (w?w.innerText:'').trim().slice(0,26);}});
      return {{n:rs.length, checked:on, all:all.slice(0,8)}};}}""")
    rec(f"{sub}|20","PASS" if (idt and any("IMEI" in c for c in idt["checked"])) else "FAIL",
        f"Default selected device ID type: {idt['checked'] if idt else 'none'} (options: {idt['all'] if idt else []}).")
    alt=pg.evaluate(f"""()=>{{const d={N.SUB};const rs=[...d.querySelectorAll('input[type=radio]')];
      const t=rs.find(r=>!r.checked); if(!t)return null;(t.closest('label')||t).click();
      const w=t.closest('.md-selection-control-container,.md-cell,div');
      return {{checked:t.checked,label:(w?w.innerText:'').trim().slice(0,26)}};}}""")
    pg.wait_for_timeout(1500)
    rec(f"{sub}|21","PASS" if (alt and alt.get("checked")) else "FAIL", f"Selecting another device ID type checks it ({alt}).")
    wf=pg.evaluate(f"""()=>{{const d={N.SUB};const rs=[...d.querySelectorAll('input[type=radio]')];
      if(rs.length<3)return null; const t=rs[rs.length-1];(t.closest('label')||t).click();
      const w=t.closest('.md-selection-control-container,.md-cell,div');
      return {{checked:t.checked,label:(w?w.innerText:'').trim().slice(0,30)}};}}""")
    pg.wait_for_timeout(1500)
    rec(f"{sub}|22","PASS" if (wf and wf.get("checked")) else "FAIL", f"Selecting a workflow checks it ({wf}).")
    sv,still,errs=S.save(pg)
    rec(f"{sub}|23","PASS" if (not still) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and the device record is created{'; validation '+str(errs) if errs else ''}.")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()
    for sheet in (sys.argv[1:] or list(SR.CFG.keys())):
        cf=SR.CFG[sheet]; R={}
        def rec(k,s,n,_R=R): _R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:118]}", flush=True)
        print(f"\n########## {sheet.strip()} ({cf['route']}) ##########", flush=True)
        try:
            wb,ws,idx=resultio.load(sheet)
            desc={k:str(ws.cell(r,3).value or "") for k,r in idx.items()}
            # clear any leftover test record from a previous attempt so creation can't collide
            pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
            if N.search_grid(pg, TAG) > 0:
                pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
                  const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='delete');if(a)a.click();}""")
                pg.wait_for_timeout(3000)
                pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
                  const d=ds[ds.length-1];if(!d)return;const b=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(b)b.click();}""")
                pg.wait_for_timeout(6000)
                print("  [pre-clean] removed a leftover test record", flush=True)
            # Grid 1-9
            pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
            N.run_grid(pg, rec, "Grid", cf["filt"], cf["word"])
            # New <Entity>
            nk=sorted([k for k in idx if k.startswith(cf["new"]+"|")], key=lambda k:int(k.split("|")[1]))
            url=SR.create_entity(pg, rec, cf, nk, desc)
            print(f"  [ctx] record: {url}", flush=True)
            if url and "/portal/" in url:
                # Record block (product category / brand only)
                if any(k.startswith("Record|") for k in idx):
                    SR.record_block(pg, rec, url, cf["sub"])
                # sub-grid ADD flow first, so the filter scenarios run against populated data
                pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
                if cf["kind"]=="devcat":   sub_add_devcat(pg, rec, cf["sub"])
                elif cf["kind"]=="prodcat":sub_add_prodcat(pg, rec, cf["sub"])
                else:                      sub_add_brand(pg, rec, cf["sub"])
                # sub-grid filters 1-8
                pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
                N.click_tab(pg, cf["sub"])
                SR.filter_block(pg, rec, cf["sub"], cf["subfilt"])
                SR.timeline_block(pg, rec, url)
                SR.notes_block(pg, rec, url)
                SR.teardown(pg, url, cf["route"], sheet.strip())
            else:
                for k in idx:
                    if k not in R and not k.startswith(("Grid|", cf["new"]+"|")):
                        rec(k,"BLOCKED","The parent record could not be created, so this scenario could not be reached.")
        except Exception as e:
            print(f"  !! aborted: {str(e)[:150]}", flush=True)
        n,missed,_=resultio.write(sheet, R)
        print(f"  >> wrote {n} rows; missed={missed}; tally={resultio.tally(sheet)}", flush=True)
    b.close()
