"""Drive the simple SETTINGS tabs: Grid 1-9 (filters/search/export),
New <Entity> (description-driven), then Grid 10-14 against the record THIS run created
(so the edit/delete steps operate on our own data and double as teardown)."""
import sys, json, re
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S
from playwright.sync_api import sync_playwright

TAG="RegressionTest0817"

CFG = {
 "SETTINGS - COVERAGE TYPE ":      dict(route="/portal/coverage-type",      filt="Filter Coverage Types",      word="Coverage types",     new="New Coverage Type"),
 "SETTINGS - COVERAGE COST TYPE ": dict(route="/portal/coverage-cost-type", filt="Filter Coverage Cost Types", word="Coverage cost types",new="New Coverage Cost Type"),
 "SETTINGS - REPAIR NETWORk ":     dict(route="/portal/repair-network",     filt="Filter Repair Network",      word="Repair network",     new="New Repair Network"),
 "SETTINGS - REGIONS":             dict(route="/portal/regions",            filt="Filter Regions",             word="Regions",            new="New Region"),
 "SETTINGS - ADMINISTRATORS":      dict(route="/portal/administrators",     filt="Filter Administrators",      word="Administrators",     new="New Administrator"),
 "SETTINGS - UNDERWRITERS":        dict(route="/portal/underwriters",       filt="Filter Underwriters",        word="Underwriters",       new="New Underwriter"),
 "SETTINGS - LANGUAGE":            dict(route="/portal/languages",          filt="Filter Languages",           word="Languages",          new="New Language"),
 "SETTINGS-REVIEW QUESTIONS":      dict(route="/portal/review-questions",   filt="Filter Review Questions",    word="Review questions",   new="New Review Question"),
 "SETTINGS - SHARE":               dict(route="/portal/share/product",      filt="Filter Shares",              word="Shares",             new="New Share"),
 "SETTINGS - SUPPORT":             dict(route="/portal/support",            filt="Filter Supports",            word="Support",            new="Support"),
}

def run_tab(pg, sheet, cf, rec):
    wb, ws, idx = resultio.load(sheet)
    desc = {k: (str(ws.cell(r,3).value or "")) for k,r in idx.items()}
    new_sec = cf["new"]
    print(f"\n########## {sheet.strip()} ({cf['route']}) ##########", flush=True)

    pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)

    # ---- Grid 1-9 ----
    N.run_grid(pg, rec, "Grid", cf["filt"], cf["word"])

    # ---- New <Entity> : description driven ----
    pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    keys=sorted([k for k in idx if k.startswith(new_sec+"|")], key=lambda k:int(k.split("|")[1]))
    created=False; upload_i=0; last_opts=[]; last_md=False
    for k in keys:
        d=desc[k].lower().strip()
        try:
            if re.search(r'click .*new button|clcik new button|click new', d) or (k.endswith("|1") and "new" in d):
                N.add_new_grid(pg)
                t=N.sub_text(pg)
                rec(k,"PASS" if t else "FAIL", f"New opens the {new_sec} modal: {t[:120].replace(chr(10),' | ')}")
            elif re.search(r'(profile image|upload icon|uplaod icon|upload logo|uplaod logo|image section)', d):
                nfi=S.file_inputs(pg)
                rec(k,"PASS" if nfi>upload_i else "FAIL",
                    f"Image/upload section exposes a file input ({nfi} present); clicking it opens the OS file explorer (native dialog, not scriptable headless).")
            elif re.search(r'select (an? )?image', d):
                ok,msg=S.act_upload(pg, upload_i); upload_i+=1
                rec(k,"PASS" if ok else "FAIL", f"Selected image reflects in the section — {msg}.")
            elif re.search(r'^(input|inpout|inptu)\b', d) or d.startswith("input"):
                phrase=re.sub(r'^\w+\s+','',d)
                val=TAG
                if "iso" in phrase: val="rt"
                if "url" in phrase: val="https://example.test/done"
                if "script" in phrase: val="Regression test script"
                ok,msg=S.act_input(pg, phrase, val)
                rec(k,"PASS" if ok else "FAIL", f"{phrase.strip().capitalize()} accepts input — {msg}.")
            elif re.search(r'^(check|chek)\b', d):
                ok,msg=S.act_check(pg, d)
                rec(k,"PASS" if ok else "FAIL", f"{d.capitalize()} — {msg}.")
            elif re.search(r'click .*(field|dropdown)', d):
                ok,msg,o=S.act_open_select(pg, re.sub(r'click|field|the','',d))
                last_opts=o; last_md=("md-select" in msg)
                rec(k,"PASS" if o else "FAIL", f"{d.capitalize()} — {msg}; options: {o[:10]}")
            elif re.search(r'^select ', d) and "image" not in d:
                if "time format" in d:
                    ok,msg=S.act_radio(pg, d)
                    rec(k,"PASS" if ok else "FAIL", f"{d.capitalize()} — {msg}.")
                else:
                    ok,msg=S.act_pick(pg, md=last_md)
                    rec(k,"PASS" if ok else "FAIL", f"Selected '{msg}' reflects on the field.")
            elif re.search(r'save', d):
                r,still,errs=S.save(pg)
                created = (not str(r).startswith('none')) and not still
                listed=False
                if created:
                    pg.wait_for_timeout(2500); N.search_grid(pg, TAG)
                    listed=pg.locator(".md-table-row.table-row").count()>0
                rec(k,"PASS" if (created and listed) else "FAIL",
                    f"Save ('{r}') closes the modal and the new record appears in the grid (listed={listed}{'; validation '+str(errs) if errs else ''}).")
            else:
                rec(k,"FAIL", f"Unhandled step description: {desc[k][:80]}")
        except Exception as e:
            rec(k,"FAIL", f"{desc[k][:60]} — error: {str(e)[:90]}")

    # ---- Grid 10-14 against OUR record ----
    g10=f"Grid|10"
    if g10 in idx:
        pg.goto(N.BASE+cf["route"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        found=N.search_grid(pg, TAG)
        opened=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));
          (a||r).click();return 'ok';}""")
        pg.wait_for_timeout(6000)
        got=N.sub_text(pg) or ""
        rec("Grid|10","PASS" if (found>0 and opened=="ok" and got) else "FAIL",
            f"Clicking our test record on the grid opens its record/modal ({found} row(s) matched '{TAG}'): {got[:110].replace(chr(10),' | ')}")
        edited=False; newname=TAG+"-EDIT"
        try:
            L=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=text]:not([id*=search])").first
            L.fill(newname); pg.wait_for_timeout(700); edited=(L.input_value()==newname)
        except Exception as e: print("   edit err", str(e)[:60], flush=True)
        rec("Grid|11","PASS" if edited else "FAIL", f"The record's name field accepts an edited value '{newname}' ({edited}).")
        r,still,errs=S.save(pg)
        pg.wait_for_timeout(2500)
        # NOTE: the grid search does not match hyphenated terms, so search on the
        # stable TAG and read the row text to confirm the edit landed.
        N.search_grid(pg, TAG); pg.wait_for_timeout(1200)
        rowtxt=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.split('\\n')[0].trim():'';}""")
        rec("Grid|12","PASS" if (not still and "EDIT" in rowtxt) else "FAIL",
            f"Save ('{r}') closes the modal and the change shows on the grid — row now reads '{rowtxt}'{'; validation '+str(errs) if errs else ''}.")

        def click_delete():
            return pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete/.test(e.textContent));
              if(a){a.click();return 'clicked';}return 'no-delete-action';}""")
        def confirm(which):
            return pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('md-dialog--full-page'));
              const d=ds[ds.length-1]; if(!d)return 'no-dialog';
              const b=[...d.querySelectorAll('button')].find(x=>/{which}/.test(x.textContent.trim()));
              if(b){{b.click();return 'clicked';}}return 'not-found';}}""")

        N.search_grid(pg, TAG)
        dele=click_delete(); pg.wait_for_timeout(3500)
        dlg=N.sub_text(pg) or ""
        has_yes_no = ("Yes" in dlg and "No" in dlg)
        rec("Grid|13","PASS" if (dele=="clicked" and has_yes_no) else "FAIL",
            f"Delete shows a confirmation modal offering Yes/No ({dele}): {dlg[:120].replace(chr(10),' | ')}")

        no_ok=False; gone=False
        if has_yes_no:
            confirm("No"); pg.wait_for_timeout(3000)
            no_ok = N.search_grid(pg, TAG) > 0          # No -> record survives
            click_delete(); pg.wait_for_timeout(3000)
            confirm("Yes"); pg.wait_for_timeout(6500)
            gone = N.search_grid(pg, TAG) == 0          # Yes -> record removed
        rec("Grid|14","PASS" if (no_ok and gone) else "FAIL",
            f"No dismisses the dialog and keeps the record (still listed={no_ok}); Yes deletes it (removed from grid={gone}).")
        print(f"  [teardown] {sheet.strip()}: test record removed={gone}", flush=True)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()
    only=sys.argv[1:] if len(sys.argv)>1 else list(CFG.keys())
    for sheet in only:
        cf=CFG[sheet]
        R={}
        def rec(k,s,n,_R=R): _R[k]=(s,n[:430]); print(f"  {k}: {s} — {n[:118]}", flush=True)
        try:
            run_tab(pg, sheet, cf, rec)
        except Exception as e:
            print(f"  !! {sheet} aborted: {str(e)[:140]}", flush=True)
        n,missed,_=resultio.write(sheet, R)
        print(f"  >> wrote {n} rows to {sheet.strip()}; missed={missed}; tally={resultio.tally(sheet)}", flush=True)
    b.close()
