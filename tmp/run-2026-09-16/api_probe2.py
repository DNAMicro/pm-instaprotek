"""READ-ONLY. Ask the portal's real API whether the record still exists."""
import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import plib as N
from playwright.sync_api import sync_playwright
PID="d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a"
ALIVE="Camera Protection 100"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=N.AUTH,viewport={'width':1600,'height':1100}).new_page()
    payloads=[]
    def cap(r):
        if r.method=="POST" and "/node/grid" in r.url:
            try: payloads.append(r.post_data)
            except Exception: pass
    pg.on("request", cap)
    pg.goto(N.BASE+"/portal/product-plans", wait_until="domcontentloaded", timeout=90000)
    for _ in range(45):
        pg.wait_for_timeout(3000)
        if pg.locator(".md-table-row.table-row").count()>0: break
    pg.wait_for_timeout(4000)
    print("=== POST /node/grid PAYLOAD (plans grid) ===", flush=True)
    for pl in payloads[:3]: print(" ", (pl or "")[:900], flush=True)

    print("\n=== GET /node/product_list/<deleted id> ===", flush=True)
    r=pg.evaluate("""async(u)=>{const res=await fetch(u,{credentials:'include'});
      const t=await res.text();return {s:res.status,b:t.slice(0,1200)};}""", f"/node/product_list/{PID}")
    print("  status:", r["s"], flush=True)
    print("  body:", r["b"][:1100], flush=True)

    # control: a plan we know is alive, to see what a healthy response looks like
    print("\n=== control: grid payload replayed with archived/status variants ===", flush=True)
    base = payloads[0] if payloads else None
    if base:
        try: obj=json.loads(base)
        except Exception: obj=None
        print("  parsed keys:", list(obj.keys())[:20] if isinstance(obj,dict) else "(not a dict)", flush=True)
        if isinstance(obj,dict):
            for variant in [{"status":"archived"},{"archived":True},{"is_active":False},{"isActive":False},{"includeDeleted":True},{"is_archived":True}]:
                o=dict(obj); o.update(variant)
                res=pg.evaluate("""async(args)=>{const [u,body]=args;
                  const r=await fetch(u,{method:'POST',credentials:'include',
                    headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
                  const t=await r.text();
                  let n=null; try{const j=JSON.parse(t); n=(j.total??j.count??(j.rows&&j.rows.length)??(j.data&&j.data.length));}catch(e){}
                  return {s:r.status,total:n,b:t.slice(0,220)};}""", ["/node/grid", o])
                hit = "Years Warranty Replacement" in (res["b"] or "")
                print(f"  {str(variant):28s} -> {res['s']} total={res['total']} deletedPlanInBody={hit}", flush=True)
    b.close()
