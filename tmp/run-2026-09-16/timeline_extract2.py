import sys, os; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
DL="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence/recover"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1400}).new_page()
    pg.goto(N.BASE+"/portal/timeline", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(32000)
    blocks=pg.evaluate("""()=>{
      const KEY='Years Warranty Replacement';
      const hits=[...document.querySelectorAll('*')].filter(e=>
        (e.innerText||'').includes(KEY) && e.children.length<25 && (e.innerText||'').length<1800);
      const seen=new Set(); const out=[];
      hits.forEach(e=>{const t=e.innerText.trim(); if(!seen.has(t)){seen.add(t); out.push(t);}});
      out.sort((a,b)=>a.length-b.length);
      return out;}""")
    print(f"=== {len(blocks)} block(s) containing the plan name ===", flush=True)
    for i,bl in enumerate(blocks[:8]):
        print(f"\n--- block {i} (len {len(bl)}) ---", flush=True)
        print(bl[:1600], flush=True)
    if blocks: open(DL+"/plan_timeline_entries.txt","w").write("\n\n=====\n\n".join(blocks))
    pg.screenshot(path=DL+"/timeline_plan_entries.png", full_page=True)
    b.close()
