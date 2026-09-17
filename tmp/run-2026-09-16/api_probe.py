"""READ-ONLY. Find the data API the portal uses, then ask it directly about the record."""
import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PID="d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100})
    pg=ctx.new_page()
    seen=[]
    pg.on("request", lambda r: seen.append((r.resource_type, r.method, r.url)) if r.resource_type in ("xhr","fetch") else None)
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
    for _ in range(45):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    pg.wait_for_timeout(5000)
    print("=== XHR/FETCH REQUESTS ===", flush=True)
    for rt,m,u in seen[:40]: print(f"  {m:5s} {u[:200]}", flush=True)
    if not seen: print("  (none captured — grid data may be server-rendered)", flush=True)

    # try the record's own page and capture its XHR
    seen.clear()
    pg.goto(f"{N.BASE}/portal/product-plans/{PID}", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout=getattr(pg,'wait_for_timeout'); pg.wait_for_timeout(20000)
    print("\n=== XHR ON THE DELETED RECORD'S URL ===", flush=True)
    for rt,m,u in seen[:25]: print(f"  {m:5s} {u[:200]}", flush=True)

    # ask the API endpoints directly from inside the page (carries auth cookies)
    print("\n=== DIRECT API QUERIES FOR THE RECORD ===", flush=True)
    for path in [f"/api/product-plans/{PID}", f"/api/plan/{PID}", f"/api/plans/{PID}",
                 f"/api/product-plan/{PID}", f"/api/v1/product-plans/{PID}",
                 "/api/product-plans?archived=true", "/api/product-plans?includeDeleted=true"]:
        try:
            r=pg.evaluate("""async (u)=>{try{const res=await fetch(u,{credentials:'include'});
              const t=await res.text(); return {s:res.status, b:t.slice(0,400)};}catch(e){return {s:-1,b:String(e).slice(0,120)};}}""", path)
            print(f"  {path:44s} -> {r['s']} | {r['b'][:170]}", flush=True)
        except Exception as e:
            print(f"  {path:44s} -> ERR {str(e)[:70]}", flush=True)
    b.close()
