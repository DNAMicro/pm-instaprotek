from playwright.sync_api import sync_playwright
BASE="https://crm.nullnet.instaprotek.com"
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/evidence"
CE="regressiontest_cust_20260817@qamail.test"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_context(storage_state=EV+"/auth_state.json",viewport={'width':1500,'height':1050}).new_page()
    pg.goto(BASE+"/portal/user", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(8000)
    pg.get_by_text("addNew").first.click(); pg.wait_for_timeout(4000)
    def rs(fid,text=None):
        c=pg.locator(f".md-dialog #{fid}").locator("xpath=ancestor::div[contains(@class,'Select')][1]")
        c.scroll_into_view_if_needed(); c.click(); pg.wait_for_timeout(1300)
        o=(pg.locator(".Select-menu-outer .Select-option",has_text=text).first if text else pg.locator(".Select-menu-outer .Select-option").first)
        o.wait_for(state="visible",timeout=8000); t=o.inner_text().strip(); o.click(); pg.wait_for_timeout(800); return t
    pg.locator(".md-dialog #email").fill(CE)
    pg.locator(".md-dialog #first_name").fill("RegressionTest")
    pg.locator(".md-dialog #last_name").fill("CustomerAug17")
    rs("role","Basic Client"); pg.wait_for_timeout(2500)
    # choose a NON-admin user type (End User) which likely needs no company
    pg.locator(".md-dialog #user_type-toggle").click(); pg.wait_for_timeout(1200)
    pg.locator(".md-list.md-layover-child [role=option]", has_text="End User").last.click(); pg.wait_for_timeout(1500)
    rs("country_lu","United States"); rs("phone_code","US")
    pg.locator(".md-dialog #mobile_phone").fill("4155550199")
    pg.locator(".md-dialog #password").fill("TestPass123!")
    pg.wait_for_timeout(1000)
    # click save then read validation
    pg.evaluate("""()=>{const d=document.querySelector('.md-dialog');
      const b=[...d.querySelectorAll('button')].find(x=>/Save & Close/.test(x.textContent)&&!x.disabled); if(b)b.click();}""")
    pg.wait_for_timeout(5000)
    print("dialogs:", pg.locator(".md-dialog").count())
    print("\n=== VALIDATION MESSAGES ===")
    print(pg.evaluate(r"""()=>{const d=document.querySelector('.md-dialog');if(!d)return[];
      return [...d.querySelectorAll('.md-text-field-message--error,.md-text-field-message,[class*=error]')]
        .map(e=>e.textContent.trim()).filter(Boolean);}"""))
    print("\n=== EMPTY REQUIRED (label contains *) ===")
    print(pg.evaluate(r"""()=>{const d=document.querySelector('.md-dialog');if(!d)return[];
      const out=[];
      d.querySelectorAll('input').forEach(i=>{
        const w=i.closest('.md-cell,.md-text-field-container,.md-select-field__toggle,.Select')||i.parentElement;
        const txt=(w?w.innerText:'')||'';
        const sel=i.closest('.Select');
        const val=sel?(sel.querySelector('.Select-value-label')?.textContent||''):i.value;
        if(/\*/.test(txt)&&!val) out.push({id:i.id||i.type,label:txt.split('\n')[0].slice(0,30)});
      });
      return out;}"""))
    print("\nuser_type value:", pg.evaluate("()=>document.querySelector('.md-dialog #user_type')?.value"))
    print("full dialog text:", pg.inner_text(".md-dialog")[:600].replace("\n"," | "))
    b.close()
