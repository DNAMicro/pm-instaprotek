"""Remove the test company and everything created under it (product, plan, batch)."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright

URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
TAG="RegressionTest0817"
FULL=".md-dialog--full-page"

def confirm_yes(pg, expect=("delete","remove")):
    txt=N.sub_text(pg) or ""
    if not any(w in txt.lower() for w in expect):
        return f"ABORTED (dialog did not mention {expect!r}): {txt[:80]!r}"
    r=pg.evaluate(f"""()=>{{const ds=[...document.querySelectorAll('.md-dialog')].filter(x=>!x.classList.contains('md-dialog--full-page'));
      const d=ds[ds.length-1];if(!d)return 'no-dialog';
      const y=[...d.querySelectorAll('button')].find(x=>/Yes/.test(x.textContent));
      if(y){{y.click();return 'yes';}}return 'no-yes-btn';}}""")
    pg.wait_for_timeout(7000); return r

def delete_rows_in_tab(pg, tab, label):
    """Delete every row in a company sub-tab."""
    for i in range(6):
        pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8500)
        if not N.click_tab(pg, tab): return f"{label}: tab not found"
        n=pg.evaluate(f"""()=>document.querySelectorAll('{FULL} .md-table-row.table-row').length""")
        if n==0: return f"{label}: 0 rows remaining"
        d=pg.evaluate(f"""()=>{{const r=document.querySelector('{FULL} .md-table-row.table-row');if(!r)return 'no-row';
          const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/delete|remove_circle/.test(e.textContent));
          if(a){{a.click();return 'clicked';}}return 'no-delete-action';}}""")
        pg.wait_for_timeout(3500)
        c=confirm_yes(pg)
        print(f"   {label}: row delete={d} confirm={c} (had {n})", flush=True)
        if d!='clicked': return f"{label}: no delete action on rows ({n} remain)"
    return f"{label}: still has rows after 6 attempts"

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()

    for tab,label in [("Products","products"),("Plans","plans")]:
        print(delete_rows_in_tab(pg, tab, label), flush=True)

    # now the company record itself
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    d=pg.evaluate(f"""()=>{{const dl=document.querySelector('{FULL}');if(!dl)return 'no-record';
      const b=[...dl.querySelectorAll('button')].find(x=>/^deleteDelete$|Delete$/.test(x.textContent.trim()));
      if(b){{b.click();return 'clicked';}}
      return 'buttons:'+JSON.stringify([...dl.querySelectorAll('button')].map(x=>x.textContent.trim()).slice(0,14));}}""")
    pg.wait_for_timeout(3500)
    dlg=N.sub_text(pg) or ""
    print("company delete:", d, "| confirm dialog:", dlg[:130].replace("\n"," | "), flush=True)
    c=confirm_yes(pg)
    print("company confirm:", c, flush=True)

    pg.goto(N.BASE+"/portal/company", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    left=pg.evaluate(f"""()=>[...document.querySelectorAll('.md-table-row.table-row')]
      .map(r=>r.innerText.replace(/\\s+/g,' ').trim()).filter(t=>/RegressionTest/.test(t));""")
    print("\nRegressionTest company rows remaining:", left, flush=True)

    # also confirm no stray test rows in plans / products-level grids
    for route,label in [("/portal/product-plans","plans")]:
        pg.goto(N.BASE+route, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
        hits=pg.evaluate("""()=>[...document.querySelectorAll('.md-table-row.table-row')]
          .map(r=>r.innerText.replace(/\\s+/g,' ').trim()).filter(t=>/RegressionTest/.test(t));""")
        print(f"{label} grid RegressionTest rows:", hits, flush=True)
    b.close()
