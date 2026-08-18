"""PLAN: re-do New Plan|5 (plan type default), Record|2/3 and Details|2/3 using the real
field (textarea#name), against a freshly created test plan which is deleted afterwards."""
import sys
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N, setlib as S
from playwright.sync_api import sync_playwright

SHEET="SETTINGS - PLAN "; ROUTE="/portal/product-plans"; TAG="RegressionTest0817"
PDF="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence/terms_test.pdf"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:130]}", flush=True)

def build_plan(pg):
    """Run the New Plan wizard end-to-end; returns the record URL."""
    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.add_new_grid(pg)
    # --- plan type controls (New Plan|5) ---
    pt=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      const items=[...d.querySelectorAll('.md-selection-control-container')].map(e=>{{
        const i=e.querySelector('input');
        return {{label:(e.innerText||'').replace(/radio_button_checked|radio_button_unchecked|check_box_outline_blank|check_box/g,'').trim().slice(0,24),
                 type:i?i.type:null, checked:i?i.checked:null}};}});
      const t=d.innerText; const m=t.match(/Plan Type[\\s\\S]{{0,70}}/);
      return {{items, near:m?m[0].replace(/\\n/g,' | ').slice(0,90):null}};}}""")
    checked=[i["label"] for i in (pt["items"] if pt else []) if i.get("checked")]
    rec("New Plan|5","PASS" if any("Single" in c for c in checked) else "FAIL",
        f"Default selected plan type: checked={checked}; plan-type controls offered: {[i['label'] for i in (pt['items'] if pt else [])][:4]}; form text near 'Plan Type': {pt['near'] if pt else None}")
    S.act_upload(pg,0)
    S.act_input(pg,"plan name",TAG)
    for phrase in ["region","administrator","underwriter","coverage type","coverage cost type","channel"]:
        try:
            ok,msg,o=S.act_open_select(pg,phrase)
            if o: N.rs_pick(pg)
        except Exception: pass
    S.act_input(pg,"sku","REGTEST-SKU-0817")
    S.act_input(pg,"coverage period","12")
    miss=pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return[];const out=[];
      d.querySelectorAll('input').forEach(i=>{{
        const w=i.closest('.md-cell,.md-text-field-container,.Select')||i.parentElement;
        const txt=(w?w.innerText:'')||''; const sel=i.closest('.Select');
        const val=sel?((sel.querySelector('.Select-value-label')||{{}}).textContent||''):i.value;
        if(/\\*/.test(txt)&&!val) out.push({{id:i.id||i.type,sel:!!sel}});}});return out;}}""")
    for m in miss:
        try:
            if m["sel"]: N.rs_open(pg,m["id"],".md-dialog:not(.md-dialog--full-page)"); N.rs_pick(pg)
            else: pg.locator(f".md-dialog:not(.md-dialog--full-page) #{m['id']}").fill("1")
            pg.wait_for_timeout(400)
        except Exception: pass
    N.sub_click(pg,"Next"); pg.wait_for_timeout(6500)
    try:
        ok,msg,o=S.act_open_select(pg,"support")
        if o: N.rs_pick(pg)
    except Exception: pass
    try:
        pg.locator(".md-dialog:not(.md-dialog--full-page) input[type=file]").last.set_input_files(PDF); pg.wait_for_timeout(3500)
    except Exception: pass
    N.sub_click(pg,"Next"); pg.wait_for_timeout(6500)
    S.save(pg); pg.wait_for_timeout(3000)
    return pg.url if "/product-plans/" in pg.url else None

def save_record(pg):
    r=pg.evaluate("""()=>{const d=document.querySelector('.md-dialog--full-page');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
            ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
      if(b){b.click();return b.textContent.trim();}return 'none';}""")
    pg.wait_for_timeout(7000); return r

def grid_row_for(pg, term):
    pg.goto(N.BASE+ROUTE, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    try:
        s=pg.get_by_placeholder("Search Plans...")
        s.first.fill(term); pg.wait_for_timeout(5000)
    except Exception: pass
    return pg.evaluate("""()=>{const rs=[...document.querySelectorAll('.md-table-row.table-row')]
        .map(r=>r.innerText.replace(/\\s+/g,' ').trim()).filter(t=>/RegressionTest/.test(t));
      return rs[0]||'';}""")

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100},accept_downloads=True).new_page()
    url=build_plan(pg)
    print(f"  [ctx] plan record: {url}", flush=True)
    if url:
        # ---- Record|2 / Record|3 ----
        pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        NEW=TAG+"-EDIT"; ok=False; before=None
        try:
            L=pg.locator(".md-dialog--full-page #name")
            before=L.input_value()
            L.scroll_into_view_if_needed(); L.fill(NEW); pg.wait_for_timeout(900); ok=(L.input_value()==NEW)
        except Exception as e: print("   edit err", str(e)[:70], flush=True)
        rec("Record|2","PASS" if ok else "FAIL",
            f"The plan name field (textarea#name) accepts an updated value — '{before}' -> '{NEW}' ({ok}).")
        sv=save_record(pg)
        row=grid_row_for(pg, TAG)
        rec("Record|3","PASS" if "EDIT" in row else "FAIL",
            f"Save ('{sv}') persists the change — the plans grid row now reads '{row[:80]}'.")

        # ---- Details|2 / Details|3 ----
        pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
        N.click_tab(pg,"Details")
        V2=TAG+"-DET"; ok2=False
        try:
            L=pg.locator(".md-dialog--full-page #name")
            L.scroll_into_view_if_needed(); L.fill(V2); pg.wait_for_timeout(900); ok2=(L.input_value()==V2)
        except Exception as e: print("   det err", str(e)[:70], flush=True)
        rec("Details|2","PASS" if ok2 else "FAIL", f"A Details field accepts an updated value '{V2}' ({ok2}).")
        sv2=save_record(pg)
        row2=grid_row_for(pg, TAG)
        rec("Details|3","PASS" if "DET" in row2 else "FAIL",
            f"Save ('{sv2}') persists the details change — grid row reads '{row2[:80]}'.")

        # ---- teardown ----
        pg.goto(url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        d=pg.evaluate("""()=>{const dl=document.querySelector('.md-dialog--full-page');
          const b=[...dl.querySelectorAll('button')].find(x=>/Delete/i.test(x.textContent));
          if(b){b.click();return 'clicked';}return 'no-delete';}""")
        pg.wait_for_timeout(3500)
        txt=N.sub_text(pg) or ""
        if "Yes" in txt:
            pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
              const d=ds[ds.length-1];const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));if(y)y.click();}}""")
            pg.wait_for_timeout(7000)
        left=grid_row_for(pg, TAG)
        print(f"  [teardown] delete={d}; leftover row={left!r}", flush=True)
    b.close()

n,missed,_=resultio.write(SHEET,R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally(SHEET)}")
