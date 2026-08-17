import sys, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
from playwright.sync_api import sync_playwright

BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
R={}
def rec(k,s,n): R[k]=(s,n[:400]); print(f"  {k}: {s} — {n[:140]}", flush=True)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)

    def rs(fid):
        c=pg.locator(f".md-dialog #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
        c.scroll_into_view_if_needed(); c.click(); pg.wait_for_timeout(1500)
        return pg.evaluate("()=>[...document.querySelectorAll('.Select-menu-outer .Select-option')].map(e=>e.textContent.trim())")
    def pick(txt=None):
        o=(pg.locator(".Select-menu-outer .Select-option", has_text=txt).first if txt
           else pg.locator(".Select-menu-outer .Select-option").first)
        t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(900); return t
    def valof(fid):
        return pg.evaluate(f"""()=>{{const i=document.querySelector('.md-dialog #{fid}');
          if(!i)return null;const s=i.closest('.Select');
          return s?(s.querySelector('.Select-value-label')?.textContent.trim()||null):i.value;}}""")

    # select the role that exposes contact fields
    rs("role"); role=pick("Basic Client")
    pg.wait_for_timeout(2500)
    print(f"  [setup] role set to '{role}' — contact fields now rendered", flush=True)

    # --- 12: country dropdown options ---
    co=rs("country_lu")
    rec("New User|12","PASS" if co else "FAIL",
        f"Country field opens a dropdown listing {len(co)} countries: {co}. (Field renders for the Basic Client role, which is the role that carries customer contact details.)")
    ctry=pick("United States") if any("United States" in x for x in co) else pick()
    rec("New User|13","PASS" if valof("country_lu") else "FAIL",
        f"Selected country '{ctry}' reflects on the field (reads '{valof('country_lu')}').")

    # --- 14/15: country code ---
    cc=rs("phone_code")
    rec("New User|14","PASS" if cc else "FAIL",
        f"Country Code field opens a dropdown of dial codes ({len(cc)} options); first 12: {cc[:12]}.")
    ccv=pick()
    rec("New User|15","PASS" if valof("phone_code") else "FAIL",
        f"Selected country code '{ccv}' reflects on the field (reads '{valof('phone_code')}').")

    # --- 16: phone number ---
    ph=pg.locator(".md-dialog #mobile_phone")
    ph.fill("4155551234"); pg.wait_for_timeout(800)
    got=ph.input_value()
    rec("New User|16","PASS" if got else "FAIL", f"Phone Number input accepts entry and reflects '{got}'.")

    # cross-check: does the selected country auto-align the dial code? (INSTA-1398 on QA)
    align={"country":valof("country_lu"),"code":valof("phone_code")}
    print("  [note] country/dial-code pairing observed:", align, flush=True)
    json.dump(align, open(EV+"/users/country_code_pairing.json","w"), indent=1)

    # close WITHOUT saving — no second test record created
    pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const c=[...d.querySelectorAll('button')].find(x=>/Cancel|close/i.test(x.textContent));if(c)c.click();}""")
    pg.wait_for_timeout(2500)
    print("  [cleanup] New User form closed without saving (no extra record created)", flush=True)
    pg.screenshot(path=EV+"/users/contact_fields.png")
    b.close()

n,missed,_=resultio.write("USERS", R)
print(f"\nrewrote {n} rows; missed={missed}")
print("USERS TALLY:", resultio.tally("USERS"))
