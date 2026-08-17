import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
import json
SHOP_URL=json.load(open(N.EV+"/shop_ctx.json"))["shop_url"]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    # 1) shop grid row count
    pg.goto(N.BASE+"/portal/shop", wait_until="domcontentloaded", timeout=60000)
    for t in (8,14,22):
        pg.wait_for_timeout(8000 if t==8 else 6000 if t==14 else 8000)
        print(f"  shop grid @~{t}s rows={pg.locator('.md-table-row.table-row').count()} preloader={'Getting Records' in pg.inner_text('body')}")
    print("  body:", pg.inner_text("body")[:200].replace("\n"," | "))
    # 2) open shop -> branches count
    pg.goto(SHOP_URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Branches")
    print("\n  branch rows:", pg.locator(".md-dialog--full-page .md-table-row.table-row").count())
    print("  branches text:", pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null);
      return p.map(x=>x.innerText.slice(0,220).replace(/\\n/g,' | '));}"""))
    # 3) operating hours widget inside New Branch
    N.add_new_in_record(pg)
    print("\n  === NEW BRANCH selects ===")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};if(!d)return null;
      return [...d.querySelectorAll('.Select')].map((s,i)=>({{i,
        ph:s.querySelector('.Select-placeholder')?.textContent.trim()||null,
        val:s.querySelector('.Select-value-label')?.textContent.trim()||null,
        id:s.querySelector('input')?.id||null,
        ctx:(s.closest('.md-cell,div')||{{}}).innerText?.slice(0,40).replace(/\\n/g,'|')||null}}));}}"""))
    print("\n  === all inputs ===")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};return [...d.querySelectorAll('input')].map(e=>({{id:e.id,type:e.type,vis:e.offsetParent!==null}}));}}"""))
    print("\n  === operating hours area text ===")
    print(pg.evaluate(f"""()=>{{const d={N.SUB};const t=d.innerText;const i=t.indexOf('Operating');
      return i<0?'none':t.slice(i,i+240).replace(/\\n/g,' | ');}}"""))
    # 4) timeline
    pg.goto(SHOP_URL, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    N.click_tab(pg,"Timeline"); pg.wait_for_timeout(6000)
    print("\n  timeline rows:", pg.locator(".md-dialog--full-page .md-table-row.table-row").count())
    print("  timeline panel:", pg.evaluate("""()=>{const p=[...document.querySelectorAll('.md-tab-panel')].filter(x=>x.offsetParent!==null);
      return p.map(x=>x.innerText.slice(0,300).replace(/\\n/g,' | '));}"""))
    print("  search inputs in record:", pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog--full-page input')].map(e=>({id:e.id,ph:e.placeholder,vis:e.offsetParent!==null}))"""))
    b.close()
