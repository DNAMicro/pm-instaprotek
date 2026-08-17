import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    N.add_new_grid(pg); pg.wait_for_timeout(4500)
    pg.locator(".md-dialog:not(.md-dialog--full-page) .datatable--radioSelect").first.click(); pg.wait_for_timeout(3000)
    JS = """()=>{const d=%s;
      const heads=[...d.querySelectorAll('*')].filter(e=>/^Step \\d/.test(e.textContent.trim())&&e.children.length<=2);
      return heads.map(h=>{
        // content = text of the parent block minus the heading itself
        const par=h.parentElement;
        const txt=(par?par.innerText:'').replace(h.textContent,'').trim();
        return {head:h.textContent.trim().slice(0,30), visible:h.offsetParent!==null,
                content:txt.slice(0,180).replace(/\\n/g,' | '),
                inputs:par?[...par.querySelectorAll('input')].filter(i=>i.offsetParent!==null&&i.type!=='hidden').map(i=>i.id||i.type).slice(0,10):[]};});}""" % N.SUB
    print("=== PER-STEP SECTIONS (after selecting a registration) ===")
    for s in pg.evaluate(JS):
        print(f"\n  {s['head']}  visible={s['visible']}")
        print(f"     inputs: {s['inputs']}")
        print(f"     content: {s['content'][:170]}")
    print("\n=== where are No/Yes after Next? ===")
    pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);if(b)b.click();}}""")
    pg.wait_for_timeout(6000)
    print(pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog')].map(d=>({
       full:d.classList.contains('md-dialog--full-page'),
       cls:d.className.slice(0,60),
       btns:[...d.querySelectorAll('button')].map(b=>b.textContent.trim()).slice(-4),
       head:d.innerText.slice(0,90).replace(/\\n/g,' | ')}))"""))
    print("\n>>> declining (No) — will not submit a real claim")
    pg.evaluate("""()=>{const ds=[...document.querySelectorAll('.md-dialog')];
      for(const d of ds){const b=[...d.querySelectorAll('button')].find(x=>/No$/.test(x.textContent.trim()));if(b){b.click();return;}}}""")
    pg.wait_for_timeout(2500)
    b.close()
