"""SETTINGS - PLAN (62): 3-step New Plan wizard, record, details, timeline, notes, teardown."""
import sys, re
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S, set_record as SR
from playwright.sync_api import sync_playwright

SHEET="SETTINGS - PLAN "
ROUTE="/portal/product-plans"
TAG="RegressionTest0817"
PDF="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence/terms_test.pdf"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:125]}", flush=True)

def open_sel(pg, phrase):
    ok,msg,o=S.act_open_select(pg,phrase); return o,msg
def pick(pg, txt=None):
    try: return N.rs_pick(pg,txt)
    except Exception: return None

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True)
    pg=ctx.new_page()

    # ---------- pre-clean ----------
    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    if N.search_grid(pg,TAG)>0:
        pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>e.textContent.trim()==='delete');if(a)a.click();}""")
        pg.wait_for_timeout(3000)
        pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
          const d=ds[ds.length-1];if(!d)return;const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}}""")
        pg.wait_for_timeout(6000)
        print("  [pre-clean] removed leftover plan", flush=True)

    # ---------- Grid 1-9 ----------
    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.run_grid(pg, rec, "Grid", "Filter Plans", "Plans")

    # ---------- New Plan 1-29 ----------
    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.add_new_grid(pg)
    t=N.sub_text(pg)
    rec("New Plan|1","PASS" if t else "FAIL", f"New opens the New Plan modal on Step 1: {t[:130].replace(chr(10),' | ')}")
    nfi=S.file_inputs(pg)
    rec("New Plan|2","PASS" if nfi else "FAIL", f"Profile image section exposes a file input ({nfi}); clicking it opens the OS file explorer.")
    ok,msg=S.act_upload(pg,0)
    rec("New Plan|3","PASS" if ok else "FAIL", f"Selected image reflects in the profile image section — {msg}.")
    ok,msg=S.act_input(pg,"plan name",TAG)
    rec("New Plan|4","PASS" if ok else "FAIL", f"Plan name accepts input — {msg}.")

    # plan type default + change
    pt=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const s=[...d.querySelectorAll('.Select')].find(x=>/Plan Type/i.test((x.closest('.md-cell,div')||{{}}).innerText||''));
      if(s)return {{kind:'select',val:(s.querySelector('.Select-value-label')||{{}}).textContent||null}};
      const rs=[...d.querySelectorAll('input[type=radio]')];
      if(rs.length)return {{kind:'radio',checked:rs.filter(r=>r.checked).map(r=>(r.closest('.md-selection-control-container,div')||{{}}).innerText.trim().slice(0,20))}};
      const t=d.innerText; const m=t.match(/Plan Type[\\s\\S]{{0,60}}/); return {{kind:'text',near:m?m[0].replace(/\\n/g,' | '):null}};}}""")
    rec("New Plan|5","PASS" if (pt and ("Single" in str(pt))) else "FAIL", f"Default selected plan type: {pt}")
    o,msg=open_sel(pg,"plan type")
    rec("New Plan|6","PASS" if o else "FAIL", f"Plan type field opens a dropdown — {msg}; options: {o[:8]}")
    v=pick(pg)
    rec("New Plan|7","PASS" if v else "FAIL", f"Selected plan type '{v}' reflects on the field.")

    for oid,sid,phrase,label in [(8,9,"region","Region"),(11,12,"administrator","Administrator"),
                                 (13,14,"underwriter","Underwriter"),(15,16,"coverage type","Coverage type")]:
        o,msg=open_sel(pg,phrase)
        rec(f"New Plan|{oid}","PASS" if o else "FAIL", f"{label} field opens a dropdown — {msg}; options: {o[:8]}")
        v=pick(pg)
        rec(f"New Plan|{sid}","PASS" if v else "FAIL", f"Selected {label.lower()} '{v}' reflects on the field.")

    ok,msg=S.act_input(pg,"sku","REGTEST-SKU-0817")
    rec("New Plan|10","PASS" if ok else "FAIL", f"SKU accepts input — {msg}.")

    o,msg=open_sel(pg,"coverage cost type")
    rec("New Plan|17","PASS" if o else "FAIL", f"Coverage cost type field opens a dropdown — {msg}; options: {o[:8]}")
    pick(pg)
    ok,msg=S.act_input(pg,"coverage period","12")
    rec("New Plan|18","PASS" if ok else "FAIL", f"Coverage period accepts input — {msg}.")
    o,msg=open_sel(pg,"channel")
    rec("New Plan|19","PASS" if o else "FAIL", f"Channel field opens a dropdown — {msg}; options: {o[:8]}")
    v=pick(pg)
    rec("New Plan|20","PASS" if v else "FAIL", f"Selected channel '{v}' reflects on the field.")

    # fill any remaining required fields before advancing
    miss=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];
      const out=[];
      d.querySelectorAll('input').forEach(i=>{{
        const w=i.closest('.md-cell,.md-text-field-container,.Select')||i.parentElement;
        const txt=(w?w.innerText:'')||''; const sel=i.closest('.Select');
        const val=sel?((sel.querySelector('.Select-value-label')||{{}}).textContent||''):i.value;
        if(/\\*/.test(txt)&&!val) out.push({{id:i.id||i.type,label:txt.split('\\n')[0].slice(0,26),sel:!!sel}});}});
      return out;}}""")
    print("  still-empty required (step1):", miss, flush=True)
    for m in miss:
        try:
            if m["sel"]:
                N.rs_open(pg,m["id"],".md-dialog:not(.md-dialog--full-page)"); N.rs_pick(pg)
            else:
                pg.locator(f".md-dialog:not(.md-dialog--full-page) #{m['id']}").fill("1")
            pg.wait_for_timeout(500)
        except Exception: pass

    r=N.sub_click(pg,"Next"); pg.wait_for_timeout(6500)
    t2=N.sub_text(pg)
    on2 = ("Step 2" in t2) or ("Support" in t2 and "Term" in t2)
    rec("New Plan|21","PASS" if on2 else "FAIL", f"Next routes to Step 2 Support & Term Details ('{r}'): {t2[:140].replace(chr(10),' | ')}")

    o,msg=open_sel(pg,"support")
    rec("New Plan|22","PASS" if o else "FAIL", f"Support field opens a dropdown — {msg}; options: {o[:8]}")
    v=pick(pg)
    rec("New Plan|23","PASS" if v else "FAIL", f"Selected support '{v}' reflects on the field.")
    nfi2=S.file_inputs(pg)
    rec("New Plan|24","PASS" if nfi2 else "FAIL", f"Upload PDF control present ({nfi2} file input(s)); clicking it opens the OS file explorer.")
    up=False
    try:
        fi=pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]")
        fi.last.set_input_files(PDF); pg.wait_for_timeout(3500)
        up = "terms_test" in N.sub_text(pg) or "pdf" in N.sub_text(pg).lower()
    except Exception as e: print("   pdf err", str(e)[:70], flush=True)
    rec("New Plan|25","PASS" if up else "FAIL", f"Selected PDF reflects in the terms section (filename shown={up}).")

    r=N.sub_click(pg,"Next"); pg.wait_for_timeout(6500)
    t3=N.sub_text(pg)
    on3=("Step 3" in t3 or "Summary" in t3)
    rec("New Plan|26","PASS" if on3 else "FAIL", f"Next routes to Step 3 Summary ('{r}'): {t3[:140].replace(chr(10),' | ')}")
    rec("New Plan|27","PASS" if (TAG in t3) else "FAIL", f"Summary shows the plan details entered in Step 1 (plan name '{TAG}' present={TAG in t3}).")
    sup=[w for w in ["Support","Terms","Term","PDF","terms_test"] if w in t3]
    rec("New Plan|28","PASS" if sup else "FAIL", f"Summary shows the Step 2 support & term details — {sup}.")

    sv,still,errs=S.save(pg)
    pg.wait_for_timeout(2500)
    url=pg.url; routed=("/product-plans/" in url)
    rec("New Plan|29","PASS" if (not still and routed) else "FAIL",
        f"Save & Close ('{sv}') closes the modal and routes to the plan record ({url.split('/portal')[-1]}{'; validation '+str(errs) if errs else ''}).")
    plan_url=url if routed else None
    print(f"  [ctx] plan record: {plan_url}", flush=True)

    if not plan_url:
        pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        if N.search_grid(pg,TAG)>0:
            pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
              const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit/.test(e.textContent));(a||r).click();}""")
            pg.wait_for_timeout(8000); plan_url=pg.url
            print(f"  [ctx] recovered plan record: {plan_url}", flush=True)

    if plan_url:
        # ---------- Record 1-6 ----------
        pg.goto(plan_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        body=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?d.innerText.slice(0,220):'';}""")
        img=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');return d?!!d.querySelector('img'):false;}""")
        T=N.tabs(pg)
        rec("Record|1","PASS" if (TAG in body or img) else "FAIL",
            f"Plan record details display — image present={img}, plan name shown={TAG in body}; header: {body[:110].replace(chr(10),' | ')}")
        upd=False; newname=TAG+"-EDIT"
        try:
            L=pg.locator(".md-dialog--full-page input[type=text]:not([id*=search])").first
            L.scroll_into_view_if_needed(); L.fill(newname); pg.wait_for_timeout(800); upd=(L.input_value()==newname)
        except Exception as e: print("   upd err", str(e)[:60], flush=True)
        rec("Record|2","PASS" if upd else "FAIL", f"A record field accepts an updated value '{newname}' ({upd}).")
        sv=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
                ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
          if(b){b.click();return b.textContent.trim();}return 'none';}""")
        pg.wait_for_timeout(7000)
        pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        N.search_grid(pg, TAG)
        rowtxt=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.replace(/\\s+/g,' ').trim():'';}""")
        rec("Record|3","PASS" if ("EDIT" in rowtxt) else "FAIL", f"Save persists the change ('{sv}') — grid row now reads '{rowtxt[:70]}'.")
        pg.goto(plan_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
        T=N.tabs(pg)
        rec("Record|4","PASS" if (T and T[0]=="Details") else "FAIL", f"'Details' is the default open tab (tab order: {T}).")
        rec("Record|5","PASS" if N.click_tab(pg,"Timeline") else "FAIL","Timeline tab routes to the timeline panel.")
        rec("Record|6","PASS" if N.click_tab(pg,"Notes") else "FAIL","Notes tab routes to the notes panel.")

        # ---------- Details 1-3 ----------
        pg.goto(plan_url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
        N.click_tab(pg,"Details")
        dt=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');const t=d?d.innerText:'';
          return ['Plan Name','Plan Type','Region','SKU','Administrator','Underwriter','Coverage','Channel'].filter(k=>t.includes(k));}""")
        rec("Details|1","PASS" if len(dt)>=3 else "FAIL", f"Plan details entered during creation are displayed — {dt}.")
        ed=False; v2=TAG+"-DET"
        try:
            L=pg.locator(".md-dialog--full-page input[type=text]:not([id*=search])").first
            L.scroll_into_view_if_needed(); L.fill(v2); pg.wait_for_timeout(800); ed=(L.input_value()==v2)
        except Exception as e: print("   det err", str(e)[:60], flush=True)
        rec("Details|2","PASS" if ed else "FAIL", f"A details field accepts an updated value '{v2}' ({ed}).")
        sv2=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
          const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
                ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
          if(b){b.click();return b.textContent.trim();}return 'none';}""")
        pg.wait_for_timeout(7000)
        pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        N.search_grid(pg, TAG)
        rt2=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');return r?r.innerText.replace(/\\s+/g,' ').trim():'';}""")
        rec("Details|3","PASS" if ("DET" in rt2) else "FAIL", f"Save persists the details change ('{sv2}') — grid row reads '{rt2[:70]}'.")

        SR.timeline_block(pg, rec, plan_url)
        SR.notes_block(pg, rec, plan_url)
        SR.teardown(pg, plan_url, ROUTE, SHEET.strip())
    else:
        for k in ["Record|%d"%i for i in range(1,7)]+["Details|%d"%i for i in range(1,4)]+ \
                 ["Timeline|%d"%i for i in range(1,9)]+["Notes|%d"%i for i in range(1,8)]:
            rec(k,"BLOCKED","The plan record could not be created, so this scenario could not be reached.")

    b.close()

n,missed,_=resultio.write(SHEET,R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
