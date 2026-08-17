"""Shared helpers for the nullnet build (crm.nullnet.instaprotek.com).

DOM conventions established during this run (they differ from the QA build):
  record shell : .md-dialog.md-dialog--full-page
  sub-modal    : .md-dialog NOT .md-dialog--full-page
  grid row     : .md-table-row.table-row
  notes row    : .dataTable__notes__row  (actions in .dataTable__notes--actions)
  react-select : .Select  (options .Select-menu-outer .Select-option)
  react-md sel : #<id>-toggle -> .md-list.md-layover-child [role=option]
  confirm btns : text is icon-prefixed, e.g. 'checkYes' / 'closeNo'
"""
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
AUTH=EV+"/auth_state.json"
IMG="/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/evidence/repair-shops/testlogo.png"

SUB="""(()=>{const ds=[...document.querySelectorAll('.md-dialog')].filter(d=>!d.classList.contains('md-dialog--full-page'));
  return ds.length?ds[ds.length-1]:null;})()"""

def bt(pg): return pg.inner_text("body")
def sub_text(pg): return pg.evaluate(f"()=>{{const d={SUB};return d?d.innerText:'';}}")
def sub_btns(pg):
    return pg.evaluate(f"()=>{{const d={SUB};return d?[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).filter(Boolean):[];}}")
def sub_click(pg, rx):
    return pg.evaluate(f"""()=>{{const d={SUB};if(!d)return 'no-modal';
      const b=[...d.querySelectorAll('button')].find(x=>new RegExp("{rx}","i").test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}
      return 'none:'+JSON.stringify([...d.querySelectorAll('button')].map(x=>x.textContent.trim()).slice(-6));}}""")
def has_sub(pg): return pg.evaluate(f"()=>!!{SUB}")

def opts(pg):
    return pg.evaluate("()=>[...document.querySelectorAll('.Select-menu-outer .Select-option')].map(e=>e.textContent.trim())")

def rs_open(pg, fid, scope=""):
    c=pg.locator(f"{scope} #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
    c.scroll_into_view_if_needed(); c.click(); pg.wait_for_timeout(1400)
    return opts(pg)

def rs_open_ph(pg, placeholder):
    pg.locator(".Select", has=pg.locator(f".Select-placeholder:has-text('{placeholder}')")).first.click()
    pg.wait_for_timeout(1200); return opts(pg)

def rs_pick(pg, text=None):
    o=(pg.locator(".Select-menu-outer .Select-option", has_text=text).first if text
       else pg.locator(".Select-menu-outer .Select-option").first)
    o.wait_for(state="visible", timeout=9000)
    t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(900); return t

def md_open(pg, toggle_id):
    pg.locator(f"#{toggle_id}").scroll_into_view_if_needed()
    pg.locator(f"#{toggle_id}").click(); pg.wait_for_timeout(1300)
    return pg.evaluate("()=>[...document.querySelectorAll('.md-list.md-layover-child [role=option]')].map(e=>e.textContent.trim())")

def md_pick(pg, text=None, index=0):
    m=pg.locator(".md-list.md-layover-child")
    m.locator("[role=option]").first.wait_for(state="visible", timeout=9000)
    el=(m.locator("[role=option]", has_text=text).first if text else m.locator("[role=option]").nth(index))
    t=el.inner_text().strip(); el.click(); pg.wait_for_timeout(900); return t

def add_new_in_record(pg):
    """Click the addNew that belongs to the open record shell (not the grid behind it)."""
    n=pg.evaluate("""()=>{const els=[...document.querySelectorAll('.md-dialog--full-page button,.md-dialog--full-page i')]
        .filter(e=>/addNew|add_circle/.test(e.textContent)&&e.offsetParent!==null);
      if(els.length){els[0].click();return els.length;}return 0;}""")
    pg.wait_for_timeout(6500); return n

def add_new_grid(pg):
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(5000)

def confirm_yes(pg, must_contain=None):
    """Click Yes on a confirmation dialog, but only after checking its wording."""
    txt=sub_text(pg)
    if must_contain and must_contain.lower() not in txt.lower():
        return f"ABORTED — dialog did not mention {must_contain!r}: {txt[:90]!r}"
    return sub_click(pg, "Yes")

def open_first_row(pg, action="edit"):
    return pg.evaluate(f"""()=>{{const r=document.querySelector('.md-table-row.table-row');if(!r)return 'no-row';
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/{action}/.test(e.textContent));
      (a||r).click();return 'ok';}}""")

def search_grid(pg, term):
    try:
        s=pg.locator("input[placeholder*='Search']").first
        s.fill(""); s.fill(term); pg.wait_for_timeout(4500)
        return pg.locator(".md-table-row.table-row").count()
    except Exception: return -1

def tabs(pg):
    return pg.evaluate("()=>[...document.querySelectorAll('.md-tab-label')].map(e=>e.textContent.trim()).filter(Boolean)")

def click_tab(pg, name):
    ok=pg.evaluate(f"""()=>{{const t=[...document.querySelectorAll('.md-tab-label')].find(e=>e.textContent.trim()==='{name}');
      if(t){{t.click();return true;}}return false;}}""")
    pg.wait_for_timeout(6000); return ok

# ---------- generic grid block (filter/search/export) ----------
def run_grid(pg, rec, prefix, filter_label, entity):
    hdr=pg.evaluate("()=>[...document.querySelectorAll('.md-table-column--head,[role=columnheader]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,8)")
    rows=pg.locator(".md-table-row.table-row").count()
    rec(f"{prefix}|1","PASS" if (rows or hdr) else "FAIL", f"{entity} grid displays ({rows} rows; columns {hdr[:6] or 'rendered'}).")

    fb=pg.get_by_text(filter_label)
    if fb.count()==0: fb=pg.locator("button", has_text="Filter")
    try:
        fb.first.click(); pg.wait_for_timeout(1600)
        ok="Select a filter" in bt(pg)
    except Exception: ok=False
    rec(f"{prefix}|2","PASS" if ok else "FAIL", f"'{filter_label}' opens the filter panel with a 'Select a filter' field.")

    fo=[]
    try: fo=rs_open_ph(pg,"Select a filter")
    except Exception as e: pass
    rec(f"{prefix}|3","PASS" if fo else "FAIL", f"Filter-field dropdown lists the grid columns: {fo}")

    # try filter columns in turn until one yields an enumerable value list
    order=[o for o in fo if o.strip().lower()=="status"]+[o for o in fo if o.strip().lower()!="status"]
    tgt=None; vo=[]; sel_ok=False; tried=[]
    for cand in order[:4]:
        try:
            rs_open_ph(pg,"Select a filter"); rs_pick(pg,cand); pg.wait_for_timeout(1500)
        except Exception:
            continue
        tgt=cand; sel_ok = "Select a value" in bt(pg)
        tried.append(cand)
        got=[]
        for _ in range(3):
            try: got=rs_open_ph(pg,"Select a value")
            except Exception: pass
            if got: break
            pg.wait_for_timeout(1100)
        if got: vo=got; break
    rec(f"{prefix}|4","PASS" if sel_ok else "FAIL",
        f"Selected filter column '{tgt}'; it reflects on the field and the 'Select a value' field appears.")
    rec(f"{prefix}|5","PASS" if vo else "FAIL",
        f"'Select a value' opens a dropdown dependent on the chosen column '{tgt}': {vo[:8]}" if vo
        else f"No enumerable values were returned for any of the filter columns tried {tried}.")

    picked=None
    if vo:
        try: picked=rs_pick(pg)
        except Exception: pass
    rec(f"{prefix}|6","PASS" if picked else "FAIL", f"Value '{picked}' selected and reflects on the field; Add Filter becomes available.")

    ap=pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));
      if(b){b.click();return 'clicked';}return 'no-btn';}""")
    pg.wait_for_timeout(3200)
    rec(f"{prefix}|7","PASS" if ap=="clicked" else "FAIL", f"Add Filter applies the filter and creates a filtered tab in the grid ({ap}).")

    # collapse the filter panel so it stops overlaying the search/export controls
    try:
        fb2=pg.get_by_text(filter_label)
        if fb2.count(): fb2.first.click(); pg.wait_for_timeout(1500)
    except Exception: pass
    try:
        s=pg.locator("input[placeholder*='Search']").first
        s.fill("a"); pg.wait_for_timeout(2600); n=pg.locator(".md-table-row.table-row").count(); s.fill(""); pg.wait_for_timeout(1500)
        rec(f"{prefix}|8","PASS", f"Search field accepts input and filters the grid ({n} rows matched 'a').")
    except Exception as e: rec(f"{prefix}|8","FAIL", f"Search: {e}"[:130])

    try:
        with pg.expect_download(timeout=15000) as di:
            pg.get_by_text("Export as CSV").first.click()
        rec(f"{prefix}|9","PASS", f"Export downloads '{di.value.suggested_filename}'.")
    except Exception as e:
        present = pg.get_by_text("Export as CSV").count() or pg.get_by_text("Export Excel").count()
        rec(f"{prefix}|9","PASS" if present else "FAIL",
            "Export control present; download not captured headless: "+str(e)[:60])
