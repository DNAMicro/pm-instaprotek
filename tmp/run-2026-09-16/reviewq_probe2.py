"""READ-ONLY. Try BOTH edit controls and a plain row click on Review Questions."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
def load(pg):
    pg.goto(N.BASE+"/portal/review-questions", wait_until="domcontentloaded", timeout=90000)
    for _ in range(50):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: return True
    return False
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1200}).new_page()
    load(pg)
    meta=pg.evaluate("""()=>{const r=document.querySelector('.md-table-row.table-row');
      return [...r.querySelectorAll('button,i.material-icons')].map(e=>({t:e.textContent.trim(),
        tag:e.tagName, cls:(e.className||'').toString().slice(0,60), vis:e.offsetParent!==null,
        rect:(()=>{const b=e.getBoundingClientRect();return [Math.round(b.x),Math.round(b.y),Math.round(b.width)];})()}));}""")
    print("controls on row 0:")
    for m in meta: print("   ", m)
    for which in [1,0]:
        load(pg)
        r=pg.evaluate("""(w)=>{const r=document.querySelector('.md-table-row.table-row');
          const e=[...r.querySelectorAll('button,i.material-icons')].filter(x=>/edit/.test(x.textContent));
          if(e.length<=w) return 'only '+e.length;
          e[w].scrollIntoView({block:'center'}); e[w].click(); return 'clicked edit#'+w;}""", which)
        pg.wait_for_timeout(22000)
        info=pg.evaluate("""()=>({dlg:document.querySelectorAll('.md-dialog').length,url:location.pathname,
          txt:(document.querySelector('.md-dialog')||{innerText:''}).innerText.slice(0,200).replace(/\\s+/g,' ')})""")
        print(f"  {r} -> dlg={info['dlg']} url={info['url']} {info['txt'][:120]}")
    # plain row click via real mouse
    load(pg)
    try:
        pg.locator(".md-table-row.table-row").first.click(timeout=20000)
        pg.wait_for_timeout(20000)
        info=pg.evaluate("""()=>({dlg:document.querySelectorAll('.md-dialog').length,url:location.pathname})""")
        print("  real row click ->", info)
    except Exception as e:
        print("  real row click ERR", str(e)[:90])
    b.close()
