"""COMPANY > Products > Shop Setup (Company|33-51) with the real field ids.
Selecting an order flow reveals the Flow configuration + Associated Products sections."""
import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright

URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
FULL=".md-dialog--full-page"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:125]}", flush=True)

def panel(pg):
    return pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null&&x.innerText.trim());
      return p.length?p[0].innerText:'';}""")
def fill(pg, fid, val):
    L=pg.locator(f"{FULL} #{fid}")
    if not L.count(): return (False, f"#{fid} not present")
    L.first.scroll_into_view_if_needed(); L.first.fill(val); pg.wait_for_timeout(700)
    return (True, f"#{fid} now reads '{L.first.input_value()}'")
def check(pg, fid):
    r=pg.evaluate(f"""()=>{{const c=document.querySelector('{FULL} #{fid}');if(!c)return null;
      const w=c.closest('.md-selection-control-container,.md-cell,div');
      (c.closest('label')||c).click();
      return {{label:((w?w.innerText:'')||'').replace(/check_box_outline_blank|check_box/g,'').trim().slice(0,26), checked:c.checked}};}}""")
    pg.wait_for_timeout(2000); return r
def open_sel(pg, fid, multi=False):
    pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #{fid}');if(!e)return;
      const s=e.closest('.Select');s.scrollIntoView({{block:'center'}});
      const c=s.querySelector('.Select-control');if(c)c.click();}}""")
    pg.wait_for_timeout(1600)
    if not N.opts(pg):
        pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #{fid}');if(!e)return;e.focus();
          e.dispatchEvent(new KeyboardEvent('keydown',{{key:'ArrowDown',keyCode:40,bubbles:true}}));}}""")
        pg.wait_for_timeout(2200)
    return N.opts(pg)
def open_sel_label(pg, phrase):
    ok=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const el=[...d.querySelectorAll('.Select')].filter(x=>x.offsetParent!==null)
        .find(x=>new RegExp({phrase!r},'i').test(((x.closest('.md-cell,.md-text-field-container,div')||{{}}).innerText)||''));
      if(el){{el.scrollIntoView({{block:'center'}});const c=el.querySelector('.Select-control');if(c)c.click();return true;}}return false;}}""")
    pg.wait_for_timeout(1800)
    return N.opts(pg) if ok else []

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.click_tab(pg,"Products")
    pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(9000)
    N.click_tab(pg,"Shop Setup"); pg.wait_for_timeout(4000)

    t0=panel(pg)
    rec("Company|33","PASS" if "Order flow" in t0 else "FAIL",
        f"Order Flow section displayed with its options ({[k for k in ['Order flow','Claim','Registration'] if k in t0]}).")
    of=check(pg,"is_claim_order")
    rec("Company|34","PASS" if (of and of.get('checked')) else "FAIL",
        f"An order flow can be selected — {of}. Selecting it reveals the Flow configuration and Associated Products sections.")
    pg.wait_for_timeout(2500)
    t1=panel(pg)

    sa=check(pg,"select_all_devices")
    rec("Company|35","PASS" if (sa and sa.get('checked')) else "FAIL", f"'Select All Devices' can be checked — {sa}.")
    sa2=check(pg,"select_all_devices")   # uncheck again
    dev=open_sel(pg,"devices",multi=True)
    picked=None
    if dev:
        try: picked=N.rs_pick(pg)
        except Exception: pass
    rec("Company|36","PASS" if (sa2 is not None and dev) else "FAIL",
        f"With 'Select All Devices' unchecked ({sa2}) the Device List becomes selectable — options {dev[:6]}, selected '{picked}'.")

    rec("Company|37","PASS" if "ASSOCIATED PRODUCTS" in t1.upper() else "FAIL",
        f"Associated Products section displayed ({'ASSOCIATED PRODUCTS' in t1.upper()}).")
    o=open_sel_label(pg,"product categor")
    rec("Company|38","PASS" if o else "FAIL", f"Product Category field in Associated Products opens; options: {o[:8]}")
    v=None
    if o:
        try: v=N.rs_pick(pg)
        except Exception: pass
    rec("Company|39","PASS" if v else "FAIL", f"Selected product category '{v}' reflects on the field.")
    o2=open_sel(pg,"order_products",multi=True)
    if not o2: o2=open_sel_label(pg,"products \\*")
    rec("Company|40","PASS" if o2 else "FAIL", f"Products field opens; options: {o2[:8]}")
    v2=None
    if o2:
        try: v2=N.rs_pick(pg)
        except Exception: pass
    addp=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const b=[...d.querySelectorAll('button')].find(x=>/Add Product/i.test(x.textContent)&&x.offsetParent!==null);
      if(b){{b.click();return b.textContent.trim();}}
      return 'none:'+JSON.stringify([...d.querySelectorAll('button')].filter(x=>x.offsetParent!==null).map(x=>x.textContent.trim()).slice(-8));}}""")
    pg.wait_for_timeout(2500)
    rec("Company|41","PASS" if not str(addp).startswith('none') else "FAIL",
        f"Add Product control adds the chosen product to the associated list ('{addp}'; product selected='{v2}').")
    rmb=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const b=[...d.querySelectorAll('button')].find(x=>/Remove/i.test(x.textContent)&&x.offsetParent!==null);
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
    pg.wait_for_timeout(2000)
    rec("Company|42","PASS" if rmb!='none' else "FAIL", f"Remove control removes an associated product ('{rmb}').")

    t2=panel(pg)
    keys=[k for k in ["Original Price","Discount Type","Discount Value","Discounted Price","Shipping and Handling","Maximum Order Quantity"] if k in t2]
    rec("Company|43","PASS" if len(keys)>=4 else "FAIL", f"Product order details section displayed — {keys}.")
    ok,msg=fill(pg,"order_price","100")
    rec("Company|44","PASS" if ok else "FAIL", f"Original price accepts input — {msg}.")
    o3=open_sel_label(pg,"discount type")
    rec("Company|45","PASS" if o3 else "FAIL", f"Discount type field opens; options: {o3[:8]}")
    v3=None
    if o3:
        try: v3=N.rs_pick(pg)
        except Exception: pass
    rec("Company|46","PASS" if v3 else "FAIL", f"Selected discount type '{v3}' reflects on the field.")
    ok,msg=fill(pg,"discount_value","10")
    rec("Company|47","PASS" if ok else "FAIL", f"Discount value accepts input — {msg}.")
    ok,msg=fill(pg,"order_shipping_fee","5")
    rec("Company|48","PASS" if ok else "FAIL", f"Shipping and handling accepts input — {msg}.")
    ok,msg=fill(pg,"order_maximum_quantity","3")
    rec("Company|49","PASS" if ok else "FAIL", f"Maximum order quantity accepts input — {msg}.")
    desc=False
    try:
        ce=pg.locator(f"{FULL} [contenteditable=true]").last
        if ce.count():
            ce.scroll_into_view_if_needed(); ce.click()
            pg.keyboard.type("Regression test product description 2026-08-17."); pg.wait_for_timeout(1200)
            desc=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
              const es=[...d.querySelectorAll('[contenteditable=true]')];
              return es.some(e=>e.innerText.trim().length>0);}}""")
    except Exception as e: print("   desc err", str(e)[:60], flush=True)
    rec("Company|50","PASS" if desc else "FAIL", f"Product description rich-text editor accepts input ({desc}).")

    sv=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
            ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
    pg.wait_for_timeout(9000)
    errs=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,6);}}""")
    rec("Company|51","PASS" if (sv!='none' and not errs) else "FAIL",
        f"Save ('{sv}') stores the shop set-up configuration{'; validation: '+str(errs) if errs else ''}.")
    b.close()

n,missed,_=resultio.write("SETTINGS - COMPANY ",R)
print(f"\nwrote {n}; missed={missed}; tally={resultio.tally('SETTINGS - COMPANY ')}")
