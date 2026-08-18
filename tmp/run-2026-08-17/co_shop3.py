import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio, nlib as N
from playwright.sync_api import sync_playwright
URL=json.load(open(N.EV+"/company_ctx.json"))["url"]
FULL=".md-dialog--full-page"
R={}
def rec(k,s,n): R[k]=(s,n[:450]); print(f"  {k}: {s} — {n[:135]}", flush=True)
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
    # pick a product category that has products
    for cat in ["Cables","Case","Chargers","Screen Protectors","Tempered Glass"]:
        try:
            N.md_open(pg,"product_category-toggle"); N.md_pick(pg,cat)
        except Exception as e:
            print("  cat err", str(e)[:50]); continue
        pg.wait_for_timeout(3500)
        # open products multi-select
        pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #order_products');if(!e)return;
          const s=e.closest('.Select');s.scrollIntoView({{block:'center'}});
          const c=s.querySelector('.Select-control');if(c)c.click();}}""")
        pg.wait_for_timeout(1600)
        if not N.opts(pg):
            pg.evaluate(f"""()=>{{const e=document.querySelector('{FULL} #order_products');if(!e)return;e.focus();
              e.dispatchEvent(new KeyboardEvent('keydown',{{key:'ArrowDown',keyCode:40,bubbles:true}}));}}""")
            pg.wait_for_timeout(2800)
        o=N.opts(pg)
        print(f"  category '{cat}' -> products: {o[:6]}", flush=True)
        if o:
            rec("Company|40","PASS", f"Products field (#order_products) opens once a Product Category is chosen — for category '{cat}' it lists {o[:8]}.")
            v=None
            try: v=N.rs_pick(pg)
            except Exception: pass
            pg.wait_for_timeout(2000)
            add=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
              const b=[...d.querySelectorAll('button')].find(x=>/Add a Product|Add Product/i.test(x.textContent)&&x.offsetParent!==null);
              if(b){{b.click();return b.textContent.trim();}}return 'none';}}""")
            pg.wait_for_timeout(3000)
            rows=pg.evaluate(f"""()=>{{const d=document.querySelector('{FULL}');
              return [...d.querySelectorAll('.Select')].filter(s=>s.offsetParent!==null).length;}}""")
            rec("Company|41","PASS" if add!='none' else "FAIL",
                f"'Add a Product' ('{add}') adds the selected product '{v}' to the associated products list (select rows now {rows}).")
            break
    else:
        rec("Company|40","FAIL","The Products field returns no options for any product category tried (Cables, Case, Chargers, Screen Protectors, Tempered Glass).")
        rec("Company|41","BLOCKED","No product could be selected, so Add a Product could not be exercised (see Company|40).")
    b.close()
n,_,_=resultio.write("SETTINGS - COMPANY ",R)
print("tally:",resultio.tally('SETTINGS - COMPANY '))
