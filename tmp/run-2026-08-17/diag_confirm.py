import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(11000)
    N.add_new_grid(pg); pg.wait_for_timeout(4500)
    pg.locator(".md-dialog:not(.md-dialog--full-page) .datatable--radioSelect").first.click(); pg.wait_for_timeout(3000)
    pg.evaluate(f"""()=>{{const d={N.SUB};const b=[...d.querySelectorAll('button')].find(x=>/Next/i.test(x.textContent)&&!x.disabled);if(b)b.click();}}""")
    pg.wait_for_timeout(6500)
    print("=== text immediately around the Yes/No buttons ===")
    print(pg.evaluate("""()=>{const btn=[...document.querySelectorAll('button')].find(b=>/checkYes|^Yes$/.test(b.textContent.trim()));
      if(!btn)return 'no yes button';
      let e=btn, chain=[];
      for(let i=0;i<5&&e;i++){ e=e.parentElement; if(e) chain.push(e.innerText.slice(0,260).replace(/\\n/g,' | ')); }
      return chain;}"""))
    print("\n=== any element containing a question mark near the buttons ===")
    print(pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog *')]
      .filter(e=>/\\?/.test(e.textContent)&&e.children.length<3)
      .map(e=>e.textContent.trim().slice(0,140)).slice(0,8)"""))
    print("\n=== dialog title / heading elements ===")
    print(pg.evaluate("""()=>[...document.querySelectorAll('.md-dialog h1,.md-dialog h2,.md-dialog h3,.md-dialog .md-title,.md-dialog .md-subheading-2')]
      .map(e=>e.textContent.trim()).filter(Boolean).slice(0,10)"""))
    print("\n>>> declining (No)")
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/^closeNo$|^No$/.test(x.textContent.trim()));if(b)b.click();}""")
    pg.wait_for_timeout(2500)
    print("after No — buttons:", N.sub_btns(pg)[-5:])
    b.close()
