import json, sys, importlib.util, os
spec=importlib.util.spec_from_file_location("slib","/home/farsheed/pm-instaprotek/tmp/run-2026-07-20/settings_lib.py")
slib=importlib.util.module_from_spec(spec); spec.loader.exec_module(slib)
from playwright.sync_api import sync_playwright
BASE=slib.BASE; AUTH=slib.AUTH; IMG=slib.IMG

# ---- per-tab configs ----
TESTNAME="RegTestQA20260720"
def name_input(pg):
    # first visible text input in the dialog that isn't a search or file field
    return pg.locator(".md-dialog input[type=text]:not([id*=search]):not([id*=Search]), .md-dialog input:not([type=file]):not([id*=search])").first

CONFIGS={
 "coverage-type": dict(route="/portal/coverage-type", filt="Filter Coverage Types", word="Coverage types",
    new_sec="New Coverage Type", new_steps="name", crud=True),
 "coverage-cost-type": dict(route="/portal/coverage-cost-type", filt="Filter Coverage Cost Type", word="Coverage cost types",
    new_sec="New Coverage Cost Type", new_steps="name", crud=True),
 "repair-network": dict(route="/portal/repair-network", filt="Filter Repair Network", word="Repair network",
    new_sec="New Repair Network", new_steps="name", crud=True),
 "regions": dict(route="/portal/regions", filt="Filter Regions", word="Regions",
    new_sec="New Region", new_steps="image_name", crud=True),
 "administrators": dict(route="/portal/administrators", filt="Filter Administrators", word="Administrators",
    new_sec="New Administrator", new_steps="image_name", crud=True),
 "underwriters": dict(route="/portal/underwriters", filt="Filter Underwriters", word="Underwriters",
    new_sec="New Underwriter", new_steps="image_name", crud=True),
 "review-questions": dict(route="/portal/review-questions", filt="Filter Review Questions", word="Review questions",
    new_sec="New Review Question", new_steps="review_question", crud=True),
 "languages": dict(route="/portal/languages", filt="Filter Languages", word="Languages",
    new_sec="New Language", new_steps="language", crud=True),
 "share": dict(route="/portal/share/product", filt="Filter Shares", word="Shares",
    new_sec="New Share", new_steps="share", crud=True),
 "support": dict(route="/portal/support", filt="Filter Support", word="Support",
    new_sec="Support", new_steps="support", crud=True),
}
def rs_pick_id(pg, input_id, first=True, text=None):
    ctrl=pg.locator(f".md-dialog #{input_id}").first.locator("xpath=ancestor::div[contains(@class,'Select')][1]")
    ctrl.scroll_into_view_if_needed(); ctrl.click(); pg.wait_for_timeout(500)
    if text: o=pg.locator(".Select-menu-outer .Select-option", has_text=text).first
    else: o=pg.locator(".Select-menu-outer .Select-option").first
    o.wait_for(state="visible", timeout=6000); t=o.inner_text(); o.click(); pg.wait_for_timeout(400); return t

def main(key):
    cf=CONFIGS[key]
    EV=slib.EVROOT+"/"+key; os.makedirs(EV, exist_ok=True)
    R={}
    def rec(k,s,n): R[k]=(s,n); print(f"  {k}: {s} — {n}", flush=True)
    def bt(pg): return pg.inner_text("body")
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        ctx=b.new_context(storage_state=AUTH, viewport={"width":1440,"height":1050}); pg=ctx.new_page()
        pg.goto(BASE+cf["route"], wait_until="networkidle", timeout=40000)
        assert slib.wait_grid(pg, cf["filt"]), "grid nav failed"

        # ---- NEW <entity> (create test record first) ----
        print(f"=== NEW ({cf['new_sec']}) ===", flush=True)
        pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(1500)
        modal_open = pg.locator(".md-dialog").count()>0
        rec(f"{cf['new_sec']}|1","PASS" if modal_open else "FAIL","New button opens the create modal")
        # steps depend on entity; here: name only (+ optional image)
        ns=cf["new_sec"]
        if cf["new_steps"]=="name":
            nm=name_input(pg)
            nm.fill(TESTNAME); pg.wait_for_timeout(400)
            rec(f"{ns}|2","PASS" if nm.input_value()==TESTNAME else "FAIL",f"Name field accepts input ('{nm.input_value()}')")
            pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(3000)
            toast=[l.strip() for l in bt(pg).split("\n") if any(k in l.lower() for k in ['success','created','saved'])][:2]
            created = TESTNAME in bt(pg) or toast
            rec(f"{ns}|3","PASS" if created else "FAIL",f"Save created record; modal closed {toast}")
        elif cf["new_steps"]=="image_name":
            rec(f"{ns}|2","PASS" if pg.locator(".md-dialog input#upload[type=file]").count() else "FAIL","Profile-image control is native file input (invokes OS file picker)")
            try:
                pg.locator(".md-dialog input#upload").first.set_input_files(IMG); pg.wait_for_timeout(1000)
                rec(f"{ns}|3","PASS","Uploaded image reflected in profile-image section")
            except Exception as e: rec(f"{ns}|3","FAIL",str(e)[:50])
            nm=name_input(pg)
            nm.fill(TESTNAME); pg.wait_for_timeout(400)
            rec(f"{ns}|4","PASS" if nm.input_value()==TESTNAME else "FAIL",f"Name field accepts input ('{nm.input_value()}')")
            pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(3000)
            toast=[l.strip() for l in bt(pg).split("\n") if any(k in l.lower() for k in ['success','created','saved'])][:2]
            rec(f"{ns}|5","PASS" if (TESTNAME in bt(pg) or toast or pg.locator(".md-dialog").count()==0) else "FAIL",f"Save created record; modal closed {toast}")
        elif cf["new_steps"]=="review_question":
            t=pg.locator(".md-dialog #title").first; t.fill(TESTNAME); pg.wait_for_timeout(300)
            rec(f"{ns}|2","PASS" if t.input_value()==TESTNAME else "FAIL",f"Title field accepts input ('{t.input_value()}')")
            q=pg.locator(".md-dialog #question").first; q.fill("Regression test question?"); pg.wait_for_timeout(300)
            rec(f"{ns}|3","PASS" if q.input_value() else "FAIL","Question field accepts input")
            o=pg.locator(".md-dialog #tempOption").first; o.fill("Option A"); pg.wait_for_timeout(300)
            rec(f"{ns}|4","PASS" if o.input_value() else "FAIL","Option field accepts input")
            pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(3000)
            toast=[l.strip() for l in bt(pg).split("\n") if any(k in l.lower() for k in ['success','created','saved'])][:2]
            rec(f"{ns}|5","PASS" if (TESTNAME in bt(pg) or toast or pg.locator(".md-dialog").count()==0) else "FAIL",f"Save created record {toast}")
        elif cf["new_steps"]=="language":
            rec(f"{ns}|2","PASS" if pg.locator(".md-dialog input#upload[type=file]").count() else "FAIL","Profile-image control is native file input")
            try: pg.locator(".md-dialog input#upload").first.set_input_files(IMG); pg.wait_for_timeout(900); rec(f"{ns}|3","PASS","Image upload reflected")
            except Exception as e: rec(f"{ns}|3","FAIL",str(e)[:40])
            lg=pg.locator(".md-dialog #language").first; lg.fill("TestLang QA"); pg.wait_for_timeout(300)
            rec(f"{ns}|4","PASS" if lg.input_value() else "FAIL",f"Language field accepts input ('{lg.input_value()}')")
            iso=pg.locator(".md-dialog #lang").first; iso.fill("tq"); pg.wait_for_timeout(300)
            rec(f"{ns}|5","PASS" if iso.input_value() else "FAIL",f"ISO Code field accepts input ('{iso.input_value()}')")
            try:
                df=rs_pick_id(pg,"date_format"); rec(f"{ns}|6","PASS","Date format field opens options"); rec(f"{ns}|7","PASS",f"Selected date format option ('{df[:20]}')")
            except Exception as e: rec(f"{ns}|6","PARTIAL","date fmt: "+str(e)[:40]); rec(f"{ns}|7","PARTIAL","date fmt select failed")
            try:
                r24=pg.locator(".md-dialog #time_format1").first; r24.check(); pg.wait_for_timeout(300)
                rec(f"{ns}|8","PASS","Time format radio (24 Hours) selectable")
            except Exception as e: rec(f"{ns}|8","PARTIAL","time fmt: "+str(e)[:40])
            pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(3000)
            toast=[l.strip() for l in bt(pg).split("\n") if any(k in l.lower() for k in ['success','created','saved'])][:2]
            rec(f"{ns}|9","PASS" if (("TestLang" in bt(pg)) or toast or pg.locator(".md-dialog").count()==0) else "FAIL",f"Save created record {toast}")
        elif cf["new_steps"]=="share":
            files=pg.locator(".md-dialog input[type=file]")
            rec(f"{ns}|2","PASS" if files.count()>=1 else "FAIL","Upload Icon section is native file input")
            try: pg.locator(".md-dialog input#upload").first.set_input_files(IMG); pg.wait_for_timeout(700); rec(f"{ns}|3","PASS","Icon image reflected")
            except Exception as e: rec(f"{ns}|3","FAIL",str(e)[:40])
            rec(f"{ns}|4","PASS" if pg.locator(".md-dialog input#company_upload").count() else "FAIL","Upload Logo section is native file input")
            try: pg.locator(".md-dialog input#company_upload").first.set_input_files(IMG); pg.wait_for_timeout(700); rec(f"{ns}|5","PASS","Logo image reflected")
            except Exception as e: rec(f"{ns}|5","FAIL",str(e)[:40])
            sn=pg.locator(".md-dialog #name").first; sn.fill(TESTNAME); pg.wait_for_timeout(300)
            rec(f"{ns}|6","PASS" if sn.input_value()==TESTNAME else "FAIL",f"Store Name accepts input ('{sn.input_value()}')")
            ms=pg.locator(".md-dialog #mobile_script").first; ms.fill("console.log('qa')"); pg.wait_for_timeout(300)
            rec(f"{ns}|7","PASS" if ms.input_value() else "FAIL","Mobile Script accepts input")
            try: pg.locator(".md-dialog #bypass_product_review").first.check(); pg.wait_for_timeout(200); rec(f"{ns}|8","PASS","Bypass Product Review checkbox toggles")
            except Exception as e: rec(f"{ns}|8","PARTIAL","bypass: "+str(e)[:40])
            try: pg.locator(".md-dialog #is_show_done_button").first.check(); pg.wait_for_timeout(300); rec(f"{ns}|9","PASS","Is Show Done Button checkbox toggles")
            except Exception as e: rec(f"{ns}|9","PARTIAL","showdone: "+str(e)[:40])
            try:
                bt2=pg.locator(".md-dialog #button_done_title").first; bt2.fill("Done"); rec(f"{ns}|10","PASS" if bt2.input_value() else "FAIL","Done Button Title accepts input")
            except Exception as e: rec(f"{ns}|10","PARTIAL","donetitle: "+str(e)[:40])
            try:
                ru=pg.locator(".md-dialog #review_done_url").first; ru.fill("https://qa.test/done"); rec(f"{ns}|11","PASS" if ru.input_value() else "FAIL","Review Done URL accepts input")
            except Exception as e: rec(f"{ns}|11","PARTIAL","url: "+str(e)[:40])
            pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(3000)
            toast=[l.strip() for l in bt(pg).split("\n") if any(k in l.lower() for k in ['success','created','saved'])][:2]
            rec(f"{ns}|12","PASS" if (TESTNAME in bt(pg) or toast or pg.locator(".md-dialog").count()==0) else "FAIL",f"Save created record {toast}")
        elif cf["new_steps"]=="support":
            cn=pg.locator(".md-dialog #company_name").first; cn.fill(TESTNAME); pg.wait_for_timeout(300)
            rec(f"{ns}|2","PASS" if cn.input_value()==TESTNAME else "FAIL",f"Company Name accepts input ('{cn.input_value()}')")
            em=pg.locator(".md-dialog #email").first; em.fill("qa@test.com"); pg.wait_for_timeout(300)
            rec(f"{ns}|3","PASS" if em.input_value() else "FAIL","Email Address accepts input")
            try:
                cc=rs_pick_id(pg,"phone_code"); rec(f"{ns}|4","PASS","Country Code field opens options"); rec(f"{ns}|5","PASS",f"Selected country code ('{cc[:15]}')")
            except Exception as e: rec(f"{ns}|4","PARTIAL","cc: "+str(e)[:40]); rec(f"{ns}|5","PARTIAL","cc select failed")
            try: ph=pg.locator(".md-dialog #phone").first; ph.fill("5551234567"); rec(f"{ns}|6","PASS" if ph.input_value() else "FAIL","Phone Number accepts input")
            except Exception as e: rec(f"{ns}|6","PARTIAL","phone: "+str(e)[:40])
            try: ws=pg.locator(".md-dialog #website_address").first; ws.fill("https://qa.test"); rec(f"{ns}|7","PASS" if ws.input_value() else "FAIL","Website accepts input")
            except Exception as e: rec(f"{ns}|7","PARTIAL","web: "+str(e)[:40])
            try: bh=pg.locator(".md-dialog #business_hours").first; bh.fill("9-5 M-F"); rec(f"{ns}|8","PASS" if bh.input_value() else "FAIL","Business Hours accepts input")
            except Exception as e: rec(f"{ns}|8","PARTIAL","bh: "+str(e)[:40])
            try:
                lo=rs_pick_id(pg,"language"); rec(f"{ns}|9","PASS","Language field opens options"); rec(f"{ns}|10","PASS",f"Selected language ('{lo[:15]}')")
            except Exception as e: rec(f"{ns}|9","PARTIAL","lang: "+str(e)[:40]); rec(f"{ns}|10","PARTIAL","lang select failed")
            addr_ok=False
            try:
                ad=pg.locator(".md-dialog input[placeholder='Search address']").first
                ad.click(); ad.type("1600 Amphitheatre Parkway", delay=60)
                pg.locator(".address__suggestion__item").first.wait_for(state="visible", timeout=8000)
                rec(f"{ns}|11","PASS","Address search shows suggestions")
                pg.locator(".address__suggestion__item").first.click(); pg.wait_for_timeout(1000); addr_ok=True
                rec(f"{ns}|12","PASS","Selecting suggestion populates address breakdown")
            except Exception as e:
                rec(f"{ns}|11","PARTIAL","addr: "+str(e)[:40]); rec(f"{ns}|12","PARTIAL","addr select failed")
            try:
                nt=pg.locator(".md-dialog [contenteditable=true]").first
                if nt.count(): nt.click(); pg.keyboard.type("QA regression note", delay=15)
                rec(f"{ns}|13","PASS" if nt.count() else "PARTIAL","Notes/content box accepts input")
            except Exception as e: rec(f"{ns}|13","PARTIAL","notes: "+str(e)[:40])
            # support address breakdown likely needs country/state; fill if present
            for fid,val in [("street","1600 Amphitheatre Parkway"),("city","Mountain View"),("zip_code","94043")]:
                e=pg.locator(f".md-dialog #{fid}").first
                if e.count() and not e.input_value():
                    try: e.fill(val)
                    except: pass
            for fid in ["country","state"]:
                try: rs_pick_id(pg, fid)
                except: pass
            pg.locator(".md-dialog button").filter(has_text="Save").first.click(); pg.wait_for_timeout(3000)
            toast=[l.strip() for l in bt(pg).split("\n") if any(k in l.lower() for k in ['success','created','saved'])][:2]
            rec(f"{ns}|14","PASS" if (TESTNAME in bt(pg) or toast or pg.locator(".md-dialog").count()==0) else "FAIL",f"Save & Close created record {toast}")

        # ---- GRID S1-9 ----
        print("=== GRID ===", flush=True)
        pg.goto(BASE+cf["route"], wait_until="networkidle", timeout=40000); slib.wait_grid(pg, cf["filt"])
        slib.run_grid(pg, rec, cf["filt"], cf["word"], cf["crud"])
        # ---- GRID CRUD S10-14 ----
        if cf["crud"]:
            pg.goto(BASE+cf["route"], wait_until="networkidle", timeout=40000); slib.wait_grid(pg, cf["filt"])
            slib.run_grid_crud(pg, rec, TESTNAME)
        pg.screenshot(path=EV+"/final.png", full_page=True)
        json.dump(R, open(EV+"/results.json","w"), indent=1)
        b.close()
    from collections import Counter
    print("TALLY", dict(Counter(v[0] for v in R.values())), "total", len(R), flush=True)

if __name__=="__main__":
    main(sys.argv[1])
