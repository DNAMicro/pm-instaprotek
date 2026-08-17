import json, sys
from playwright.sync_api import sync_playwright

BASE=None
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence/users"
AUTH=EV+"/../auth_state.json"
EMAIL="regressiontest_20260720@qamail.test"
PW="TestPass123!"

def log(*a): print(*a, flush=True)

def rs_pick(pg, input_id, text, timeout=6000):
    """react-select: open by input id's ancestor .Select, click option by text."""
    ctrl=pg.locator(f"#{input_id}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
    ctrl.scroll_into_view_if_needed()
    ctrl.click()
    opt=pg.locator(".Select-menu-outer .Select-option", has_text=text).first
    opt.wait_for(state="visible", timeout=timeout)
    opt.click()
    pg.wait_for_timeout(400)

def rs_pick_first(pg, input_id, timeout=6000):
    """react-select: open and pick the first available option; returns its text."""
    ctrl=pg.locator(f"#{input_id}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
    ctrl.scroll_into_view_if_needed(); ctrl.click()
    first=pg.locator(".Select-menu-outer .Select-option").first
    first.wait_for(state="visible", timeout=timeout)
    txt=first.inner_text().strip(); first.click(); pg.wait_for_timeout(400)
    return txt

def fill_address(pg, query="1600 Amphitheatre Parkway, Mountain View", timeout=8000):
    """Google Places autocomplete: type, wait for .pac-item suggestions, pick the first."""
    inp=pg.get_by_placeholder("Search address")
    inp.scroll_into_view_if_needed(); inp.click(); inp.fill("")
    inp.type(query, delay=80)
    # custom autocomplete: suggestions render as .address__suggestion__item
    item=pg.locator(".address__suggestion__item").first
    item.wait_for(state="visible", timeout=timeout)
    pg.wait_for_timeout(300)
    item.click()
    pg.wait_for_timeout(800)
    # address sub-form (not auto-filled): street/city/zip inputs + province
    for fid,val in [("street","1600 Amphitheatre Parkway"),("city","Mountain View"),("zip_code","94043")]:
        loc=pg.locator(f"#{fid}")
        if loc.count() and not loc.input_value():
            loc.fill(val)
    # Province: try react-select ids, then md toggle, then plain input, then label match
    prov_done=False
    for pid in ["province","state","province_lu","state_lu"]:
        if pg.locator(f"#{pid}").count():
            try:
                # react-select?
                anc=pg.locator(f"#{pid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
                if anc.count():
                    anc.click(); pg.locator(".Select-menu-outer .Select-option").first.wait_for(state="visible",timeout=5000)
                    pg.locator(".Select-menu-outer .Select-option").first.click(); prov_done=True; break
                else:
                    pg.locator(f"#{pid}").fill("California"); prov_done=True; break
            except Exception: pass
    if not prov_done:
        # md toggle fallback
        for pid in ["province","state"]:
            if pg.locator(f"#{pid}-toggle").count():
                pg.locator(f"#{pid}-toggle").click()
                pg.locator(".md-list.md-layover-child [role=option]").first.wait_for(state="visible",timeout=5000)
                pg.locator(".md-list.md-layover-child [role=option]").first.click(); prov_done=True; break
    log("    address subfields filled; province_done=", prov_done)
    pg.wait_for_timeout(400)

def md_pick(pg, toggle_id, text=None, index=0, timeout=6000):
    """react-md SelectField: click #<toggle_id>, then click option (by text or index) without letting menu close."""
    tog=pg.locator(f"#{toggle_id}")
    tog.scroll_into_view_if_needed()
    tog.click()
    # react-md options render as div[role=option] inside the OPEN layover menu
    menu=pg.locator(".md-list.md-layover-child")
    menu.locator("[role=option]").first.wait_for(state="visible", timeout=timeout)
    if text is not None:
        menu.locator("[role=option]", has_text=text).first.click()
    else:
        menu.locator("[role=option]").nth(index).click()
    pg.wait_for_timeout(500)
    # verify selection registered on the toggle; if the menu is still open, escape it
    if pg.locator(".md-list.md-layover-child").count() and pg.locator(".md-list.md-layover-child").first.is_visible():
        pg.keyboard.press("Escape"); pg.wait_for_timeout(200)

def empty_required(pg):
    """Return list of {label, for, type} for visible required (*) fields that are still empty."""
    return pg.evaluate(r"""() => {
      const out=[];
      for (const lab of document.querySelectorAll('label')) {
        if (!lab.offsetParent) continue;
        const t=lab.textContent.trim();
        if (!/\*/.test(t)) continue;
        const fid=lab.getAttribute('for');
        // find the control
        let empty=false, kind='?';
        // react-md select toggle
        const mdTog=document.querySelector('#'+CSS.escape((fid||'')+'-toggle'));
        const rsInput=fid?document.getElementById(fid):null;
        if (mdTog){ kind='md'; const val=mdTog.querySelector('.md-select-field__toggle-value, .md-text-field'); empty = !mdTog.textContent.replace(t,'').trim(); }
        else if (rsInput && rsInput.tagName==='INPUT'){ kind='input'; empty = !rsInput.value; }
        else {
          // react-select? find .Select whose input id == fid
          const sel=[...document.querySelectorAll('.Select')].find(s=>{const i=s.querySelector('input');return i&&i.id===fid;});
          if (sel){ kind='rs'; empty = !!sel.querySelector('.Select-placeholder'); }
        }
        out.push({label:t.replace(/\s+/g,' '), for:fid, kind, empty});
      }
      return out;
    }""")

def main():
    global BASE
    c=json.load(open("/home/farsheed/pm-instaprotek/credentials.json")); cfg=c[c["Env"]]
    BASE=cfg["crm_base_url"].rstrip("/")
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        ctx=b.new_context(storage_state=AUTH, viewport={"width":1440,"height":900})
        pg=ctx.new_page()
        pg.goto(BASE+"/portal/user", wait_until="networkidle", timeout=30000)
        for i in range(12):
            pg.wait_for_timeout(1500)
            body=pg.inner_text("body")
            if "@" in body and "Getting Records" not in body: break
        pg.get_by_text("New", exact=True).first.click(); pg.wait_for_timeout(1200)

        # base text fields
        pg.get_by_label("Email *").fill(EMAIL)
        pg.get_by_label("First Name").fill("Regression")
        pg.get_by_label("Last Name").fill("TestUser")
        rs_pick(pg,"role","Basic Client"); log("role set")

        # Deterministic fill order (app-required: User Type, Country, Country Code, Company, Affiliate, Phone, Password)
        steps=[
            ("user_type(md)", lambda: md_pick(pg,"user_type-toggle", text="End User")),
            ("country(rs)",   lambda: rs_pick(pg,"country_lu","United States")),
            ("language(rs)",  lambda: rs_pick_first(pg,"language")),
            ("phone_code(rs)",lambda: rs_pick(pg,"phone_code","US (+1)")),
            ("phone",         lambda: pg.get_by_label("Phone Number *").fill("5551234567")),
            ("company(rs)",   lambda: rs_pick(pg,"company","New Sample company")),
            ("affiliate(rs)", lambda: rs_pick(pg,"affiliate_id","Enterprise")),
            ("address",       lambda: fill_address(pg)),
            ("password",      lambda: pg.get_by_label("Password *").fill(PW)),
        ]
        for name, fn in steps:
            try:
                fn(); log("  set", name)
            except Exception as e:
                log("  ERR", name, "->", str(e)[:90])
        # Fill any leftover required field the app still complains about (e.g. Language)
        pg.wait_for_timeout(500)
        leftover=[r for r in empty_required(pg) if r.get('empty')]
        for r in leftover:
            if r['label'].startswith('Language'):
                try: md_pick(pg, r['for']+"-toggle", index=0); log("  language set (leftover)")
                except Exception as e: log("  ERR language", str(e)[:80])

        pg.screenshot(path=EV+"/create_ready.png", full_page=True)
        # Save
        pg.locator("button", has_text="Save & Close").first.click()
        pg.wait_for_timeout(3500)
        body=pg.inner_text("body")
        toast=[l.strip() for l in body.split("\n") if any(k in l.lower() for k in ["success","created","added","saved","already","error","invalid","required"])]
        modal_open = "Save & Close" in body and "New User" in body
        log("SAVE toast:", toast[:4])
        log("modal still open:", modal_open)
        pg.screenshot(path=EV+"/create_result.png", full_page=True)
        b.close()

