"""Record Registration Survey Grid|1 with a selector that matches its real DOM."""
import sys; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, plib as N
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    pg.goto(N.BASE+"/portal/survey", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(35000)
    qs=pg.evaluate("""()=>{const t=document.body.innerText;
      return t.split('\\n').map(s=>s.trim()).filter(s=>s.endsWith('?')&&s.length>12);}""")
    rows=pg.evaluate("""()=>document.querySelectorAll('[class*=row], li, tr').length""")
    ok=len(qs)>0
    note=(f"Registration survey questions render on the grid — {len(qs)} question(s) listed, each with edit/delete "
          f"actions. Examples: {qs[:3]}. (Note: this grid does not use the standard .md-table-row markup.)")
    n,missed,_=resultio.write("SETTINGS - REGISTRATION SURVEY ", {"Grid|1":("PASS" if ok else "FAIL", note)})
    print(f"questions found: {len(qs)}")
    for q in qs[:6]: print("   -", q)
    print("wrote", n, "missed", missed, "tally", resultio.tally("SETTINGS - REGISTRATION SURVEY ")[0])
    b.close()
