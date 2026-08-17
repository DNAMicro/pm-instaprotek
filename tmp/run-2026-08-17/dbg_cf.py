import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import nlib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1500,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/coverage-type", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(9000)
    print("tabs on grid:", pg.evaluate("""()=>[...document.querySelectorAll('.md-tab-label,[class*=tab]')].map(e=>e.textContent.trim()).filter(Boolean).slice(0,12)"""))
    info=pg.evaluate("""()=>{const els=[...document.querySelectorAll('*')].filter(e=>e.textContent.trim()==='Custom Filter'&&e.children.length===0);
      if(!els.length)return 'none';
      const e=els[0]; let chain=[];let n=e;
      for(let i=0;i<4&&n;i++){n=n.parentElement; if(n)chain.push({cls:(n.className||'').toString().slice(0,60),
         btns:[...n.querySelectorAll('button,i')].map(x=>x.textContent.trim()).slice(0,6)});}
      return {count:els.length, chain};}""")
    print("custom filter structure:", info)
    b.close()
