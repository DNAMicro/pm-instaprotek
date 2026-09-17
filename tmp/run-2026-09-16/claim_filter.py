import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1900,'height':1200}).new_page()
    pg.goto(N.BASE+"/portal/claim", wait_until="domcontentloaded", timeout=90000)
    for _ in range(50):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    pg.get_by_text("Filter Claim Reports").first.click(); pg.wait_for_timeout(6000)
    before=pg.evaluate("""()=>{const p=document.querySelector('[class*=filter],[class*=Filter]');return p?p.innerText.replace(/\\s+/g,' ').slice(0,300):document.body.innerText.slice(0,300);}""")
    print("PANEL BEFORE:", before[:260])
    cols=N.rs_open_ph(pg,"Select a filter"); print("\nCOLUMNS:", cols)
    N.rs_pick(pg,"IMEI/Serial Number"); pg.wait_for_timeout(9000)
    after=pg.evaluate("""()=>{
      const sels=[...document.querySelectorAll('.Select')].map(s=>({
        ph:(s.querySelector('.Select-placeholder')||{textContent:''}).textContent.trim(),
        val:(s.querySelector('.Select-value-label')||{textContent:''}).textContent.trim()}));
      const inputs=[...document.querySelectorAll('input')].filter(i=>i.offsetParent!==null).map(i=>({
        id:i.id, ph:i.placeholder, type:i.type}));
      const btns=[...document.querySelectorAll('button')].map(b=>b.innerText.trim()).filter(t=>/filter/i.test(t));
      return {sels, inputs:inputs.slice(0,10), btns};}""")
    print("\nAFTER PICKING 'IMEI/Serial Number':")
    print("  selects:", after["sels"])
    print("  inputs :", after["inputs"])
    print("  buttons:", after["btns"])
    txt=N.bt(pg)
    print("  'Select a value' present:", "Select a value" in txt)
    print("  'Enter a value' present:", "Enter a value" in txt)
    pg.screenshot(path=N.EV+"/claim_filter.png")
    b.close()
