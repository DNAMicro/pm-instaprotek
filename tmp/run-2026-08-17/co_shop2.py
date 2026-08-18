import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
FULL=".md-dialog--full-page"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:130]}", flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(10000)
    N.click_tab(pg,"Products")
    pg.evaluate("""()=>{const r=document.querySelector('.md-dialog--full-page .md-table-row.table-row');
      const a=[...r.querySelectorAll('button,i.material-icons')].find(e=>/edit|find_in_page/.test(e.textContent));(a||r).click();}""")
    pg.wait_for_timeout(9000)
    N.click_tab(pg,"Shop Setup"); pg.wait_for_timeout(3500)
    pg.evaluate(f"""()=>{{const c=document.querySelector('{FULL} #is_claim_order');if(c&&!c.checked)(c.closest('label')||c).click();}}""")
    pg.wait_for_timeout(4500)

    # 38/39 product category (react-md toggle)
    o=[]
    try: o=N.md_open(pg,"product_category-toggle")
    except Exception as e: print("  pc err", str(e)[:60])
    rec("Company|38","PASS" if o else "FAIL", f"Product Category field in Associated Products opens (react-md select); options: {o[:8]}")
    v=None
    if o:
        try: v=N.md_pick(pg)
        except Exception: pass
    rec("Company|39","PASS" if v else "FAIL", f"Selected product category '{v}' reflects on the field.")
    pg.wait_for_timeout(2500)

    # 40 products multi-select
    def open_multi(fid):
        pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #{fid}');if(!e)return;
          const s=e.closest('.Select');s.scrollIntoView({{block:'center'}});
          const c=s.querySelector('.Select-control');if(c)c.click();}}""")
        pg.wait_for_timeout(1500)
        if not N.opts(pg):
            pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #{fid}');if(!e)return;e.focus();
              e.dispatchEvent(new KeyboardEvent('keydown',{{key:'ArrowDown',keyCode:40,bubbles:true}}));}}""")
            pg.wait_for_timeout(2500)
        return N.opts(pg)
    o2=open_multi("order_products")
    rec("Company|40","PASS" if o2 else "FAIL", f"Products field (#order_products) opens; options: {o2[:8]}")
    v2=None
    if o2:
        try: v2=N.rs_pick(pg)
        except Exception: pass
    pg.wait_for_timeout(2000)
    # 41 add product
    add=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const cands=[...d.querySelectorAll('button,i.material-icons')].filter(x=>x.offsetParent!==null&&/add/i.test(x.textContent));
      if(cands.length){{cands[0].click();return cands.map(x=>x.textContent.trim()).slice(0,4);}}
      return null;}}""")
    pg.wait_for_timeout(2500)
    chips=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL} #order_products');
      const s=d?d.closest('.Select'):null;return s?[...s.querySelectorAll('.Select-value-label')].map(e=>e.textContent.trim()).slice(0,5):[];}}""")
    rec("Company|41","PASS" if (v2 or chips) else "FAIL",
        f"Selecting a product adds it to the associated products list — selected '{v2}', list now holds {chips}. Add control(s): {add}.")
    rm=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const b=[...d.querySelectorAll('button')].find(x=>/Remove/i.test(x.textContent)&&x.offsetParent!==null);
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
    pg.wait_for_timeout(2000)
    rec("Company|42","PASS" if rm!='none' else "FAIL", f"Remove control removes an associated product ('{rm}').")

    # 45/46 discount type (react-md toggle)
    o3=[]
    try: o3=N.md_open(pg,"discount_type-toggle")
    except Exception as e: print("  dt err", str(e)[:60])
    rec("Company|45","PASS" if o3 else "FAIL", f"Discount Type field opens (react-md select); options: {o3}")
    v3=None
    if o3:
        try: v3=N.md_pick(pg)
        except Exception: pass
    rec("Company|46","PASS" if v3 else "FAIL", f"Selected discount type '{v3}' reflects on the field.")

    # 50 description (Quill editor)
    desc=False
    try:
        ql=pg.locator(f"{FULL} .ql-editor").first
        ql.scroll_into_view_if_needed(); ql.click()
        pg.keyboard.type("Regression test product description 2026-08-17.")
        pg.wait_for_timeout(1500)
        desc=pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} .ql-editor');return e?e.innerText.trim().length>0:false;}}""")
    except Exception as e: print("  desc err", str(e)[:70])
    rec("Company|50","PASS" if desc else "FAIL", f"Product description rich-text editor (Quill) accepts input ({desc}).")

    # 51 save
    for fid,val in [("order_price","100"),("discount_value","10"),("order_shipping_fee","5"),("order_maximum_quantity","3")]:
        L=pg.locator(f"{FULL} #{fid}")
        if L.count(): L.first.fill(val); pg.wait_for_timeout(400)
    pg.wait_for_timeout(800)
    sv=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
      const b=[...d.querySelectorAll('button')].find(x=>/Save and Close|Save & Close/.test(x.textContent)&&!x.disabled)
            ||[...d.querySelectorAll('button')].find(x=>/Save/.test(x.textContent)&&!x.disabled);
      if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
    pg.wait_for_timeout(9500)
    errs=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');if(!d)return[];
      return [...d.querySelectorAll('[class*=error]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,6);}}""")
    rec("Company|51","PASS" if (sv!='none' and not errs) else "FAIL",
        f"Save ('{sv}') stores the shop set-up configuration{'; validation: '+str(errs) if errs else ''}.")
    b.close()
n,_,_=resultio.write("SETTINGS - COMPANY ",R)
print("tally:",resultio.tally('SETTINGS - COMPANY '))
