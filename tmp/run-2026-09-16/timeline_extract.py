import sys, os, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
DL="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence/recover"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1400}).new_page()
    pg.goto(N.BASE+"/portal/timeline", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(30000)
    pg.get_by_text("Filter Activity").first.click(); pg.wait_for_timeout(5000)
    N.rs_open_ph(pg,"Select a filter"); N.rs_pick(pg,"Action"); pg.wait_for_timeout(4000)
    N.rs_open_ph(pg,"Select a value"); N.rs_pick(pg,"Update Plan"); pg.wait_for_timeout(3000)
    pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Add Filter/i.test(x.textContent));if(b)b.click();}""")
    pg.wait_for_timeout(18000)
    # dump each timeline entry as its own block
    blocks=pg.evaluate("""()=>{
      const cand=[...document.querySelectorAll('div,li,section')].filter(e=>{
        const t=e.innerText||''; return t.includes('Update Plan') && t.length<2500 && e.children.length<40;});
      const seen=new Set(); const out=[];
      cand.forEach(e=>{const t=e.innerText.trim(); if(!seen.has(t)){seen.add(t); out.push(t);}});
      out.sort((a,b)=>a.length-b.length);
      return out.slice(0,6);}""")
    print("=== UPDATE PLAN TIMELINE BLOCKS ===", flush=True)
    for i,bl in enumerate(blocks):
        print(f"\n--- block {i} ---", flush=True)
        print(bl[:2500], flush=True)
    pg.screenshot(path=DL+"/timeline_update_plan.png", full_page=True)
    open(DL+"/timeline_update_plan.txt","w").write("\n\n=====\n\n".join(blocks))
    b.close()
