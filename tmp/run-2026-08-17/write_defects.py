import sys, openpyxl
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio

ENV="Nullnet (crm.nullnet.instaprotek.com) — carries live production data"
BY="Automated regression run (agentqa@dnamicro.com)"
D="2026-08-17"

# (id, linked, summary, severity, priority, steps, kind)
DEFECTS=[
("DEF-SET-01","SETTINGS - LANGUAGE / Grid|4",
 "Selecting any filter column on the Languages settings grid crashes the page to a blank screen",
 "High","P2",
 "1. Log in and go to Settings > Languages. 2. Click 'Filter Languages'. 3. Open 'Select a filter' and choose any column (Language, ISO Code, Date Format or Time Format). "
 "RESULT: the app throws 'TypeError: array[key].filter is not a function at SelectFilter.mapArrayValues' (uncaught at GetLanguageFilter) and the entire page renders blank "
 "(document body length 0, no controls); a reload is required. Reproduced on all four filter columns. The identical interaction on other settings grids (e.g. Coverage Types) works normally.",
 "bug"),

("DEF-SET-09","SETTINGS - COMPANY / record + Plans sub-grid",
 "Deleting a company and removing a plan from a company both fail with HTTP 400 and no error is shown to the user",
 "High","P2",
 "1. Settings > Company > open a company record. 2. Click Delete and confirm Yes. RESULT: DELETE /company/<id> returns HTTP 400, the confirmation dialog stays open, no error message is surfaced, and the company remains in the grid. "
 "3. Same on the company's Plans tab: click remove on a plan row and confirm Yes. RESULT: DELETE /company_plan/<id> returns HTTP 400, the plan stays attached, no error is surfaced. "
 "The user is given no indication the operation failed.",
 "bug"),

("DEF-SET-10","SETTINGS - COMPANY / record Status",
 "Company record Status selector does not apply the chosen value — a company cannot be set Inactive",
 "Medium","P3",
 "1. Settings > Company > open a company record. 2. Open the Status selector (react-md, #status-toggle) and choose 'Inactive'. "
 "RESULT: the hidden #status input still reads 'Active' — the selection never binds to form state. 3. Save. Save reports success with no validation errors, "
 "but reopening the record shows Status = Active. Combined with DEF-SET-09 this leaves no way to delete or deactivate a company.",
 "bug"),

("DEF-CLAIM-01","CLAIM REPORTS / Repair Receipt|9",
 "Covered amount field on the claim Repair Receipt tab rejects all input",
 "Medium","P3",
 "1. Claim Reports > open any claim > Repair Receipt tab. 2. Tick 'Is the customer using an insurance?'. 3. Try to enter a value in the Covered amount field (#covered_amount). "
 "RESULT: the field stays at 'USD  0.00' under every input method (Playwright fill, select-all + retype, character-by-character typing). It is a plain text input with "
 "disabled=false, readOnly=false and no maxlength/pattern. The adjacent #repair_amount field, rendered identically, accepts input normally (typing 250 gives 'USD  2.50').",
 "bug"),

("DEF-REG-01","PORTAL - REGISTRATION / Claim|5",
 "New Claim wizard: the required Notes field is not enforced — the wizard advances with it empty",
 "Medium","P3",
 "1. Registrations > open a registration > Claim tab > New. 2. Advance to Step 2. 3. Leave the Notes field empty and click Next. "
 "RESULT: the wizard advances from Step 2 to Step 3 with no validation message, even though the field is labelled 'Notes *' and the textarea #notes carries required=true. "
 "Expected: the Notes field validates and blocks progression.",
 "bug"),

("DEF-SET-03","SETTINGS - DEVICE CATEGORY / Devices|13",
 "Add Devices wizard: the Step 2 'Search Devices' field does not filter the list",
 "Medium","P3",
 "1. Settings > Device Category > open a category (e.g. Chromebook) > Devices tab > Add. 2. Select a brand and click Next. 3. Type into 'Search Devices...'. "
 "RESULT: the list never filters. Baseline 22 rows; searching '100e' -> still 22 rows (first rows unchanged); '14e' -> 22; a nonsense term 'zzzzz' -> still 22 rows after 10s. "
 "The field accepts typing but no filtering is applied.",
 "bug"),

("DEF-SET-05","SETTINGS - PRODUCT CATEGORY / Timeline|8",
 "Product Category records write no timeline entries",
 "Medium","P3",
 "1. Settings > Product Category > create a category. 2. Open it > Timeline tab (ensure the 'All Activity' filter set is selected). "
 "RESULT: 'No Results Found!' — the creation is not logged. A long-standing real category (Cables) is likewise empty. "
 "By contrast the equivalent Device Category timeline does log activity (Create Category / Update Category plus historic entries), so timeline logging works elsewhere.",
 "bug"),

("DEF-SET-02","SETTINGS - REPAIR NETWORK / Grid|5",
 "Repair Network grid filter returns no selectable values",
 "Low","P4",
 "1. Settings > Repair Network. 2. Click 'Filter Repair Network' and choose the only column offered, 'Repair Network Name'. "
 "RESULT: the dependent 'Select a value' dropdown is empty even though the grid holds a record ('TRG'). No JavaScript error is raised and the page stays usable. "
 "Expected: the value list is populated from the selected column.",
 "bug"),

("DEF-USERS-01","USERS / New User|12",
 "New User country list does not match spec — Japan, Mexico and Spain missing, Puerto Rico extra",
 "Low","P4",
 "1. Users > New. 2. Set Role = Basic Client (the role that exposes customer contact fields). 3. Open the Country dropdown. "
 "RESULT: it lists Canada, Puerto Rico, United Kingdom, United States (4). Expected per the test case: Canada, Japan, Mexico, Spain, United Kingdom, United States (6). "
 "The list is also inconsistent with the Country Code dropdown, which still offers JP (+81) and MX (+52) for countries that cannot be selected.",
 "bug"),

# ---- documented deviations: reported, NOT filed as bugs ----
("DEV-REG-01","PORTAL - REGISTRATION / Details|6-7",
 "No replace-file control for a registration's store receipt",
 "Low","P4",
 "The Store Receipt section offers only view actions (View Receipt / View Image / View Photo); input[type=file] count is 0 in both the Details tab and the View Receipt modal. "
 "The test case expects a replace-file button opening the OS file explorer. Likely test-case drift — for PM confirmation.",
 "deviation"),

("DEV-CLAIM-01","CLAIM REPORTS / Record|7-8",
 "Claim record has no 'Claim Summary' or 'Claim Status Details' tab",
 "Low","P4",
 "Tabs present: Registration, Customer Details, Location, Appointment, Claim Receipt, Repair Receipt, Repair Approval, Reimbursement Review, Payment Info, Timeline, Notes. "
 "The two tabs the test cases expect are absent and five undocumented tabs are present. Looks like a claim redesign — for PM confirmation.",
 "deviation"),

("DEV-CLAIM-02","CLAIM REPORTS / Claim Reports|11-12",
 "New Claim wizard Step 4 is 'Claim Receipt', not the 'Problem Summary' the test cases describe",
 "Low","P4",
 "Step 4 renders an InstaProtek Product Guarantee Claim summary (Claim Number, Policy Number, Customer Information, Coverage Information, Shipping/Order Details) and is read-only. "
 "No Problem Date / Problem Summary fields exist anywhere in the flow. Matches the redesign noted on the QA environment in the previous cycle — for PM confirmation.",
 "deviation"),

("DEV-SET-01","SETTINGS - PRODUCT CATEGORY / Products|9-12",
 "Product Category record has no control to add products",
 "Medium","P3",
 "The Products tab of a Product Category record exposes only 'Export as CSV' and 'Filter Products' — no add/New control in any of the categories checked "
 "(the new test category plus real categories Cables 27 products, Camera Lens 20, Case 24). Products do carry a Product Category field on the company product form, "
 "so association may be intended from the product side only — for PM confirmation.",
 "deviation"),

("DEV-SET-02","SETTINGS - PLAN / New Plan|5-7",
 "New Plan form has no 'Plan Type' field",
 "Low","P4",
 "Step 1 renders exactly: Plan Name*, Region*, Coverage Amount*, SKU, Administrator*, Underwriter*, Coverage Type*, Coverage Cost Type*, Coverage Period (Year/s)*, "
 "Coverage Type Amount*, Channel* plus the image upload. The words 'Single'/'Multiple' appear nowhere. The test cases expect a Plan Type defaulting to Single — for PM confirmation.",
 "deviation"),

("DEV-SET-03","SETTINGS - COMPANY / Details|7-8",
 "No 'Device Management System' field on the company Details form",
 "Low","P4",
 "After enabling the Enterprise Program the only dropdowns are Repair Network, Country and Country Code. A Device Management System selector does exist, but on the "
 "plan Batch modal (#integrated_company) rather than company Details — the field appears to have moved. For PM confirmation.",
 "deviation"),

("DEV-SET-04","SETTINGS - COMPANY / Users|10",
 "No resend-invite action on the company users grid",
 "Low","P4",
 "A populated company (C2 Wireless, 1 user) exposes only edit / lock / remove_circle row actions. The test case expects a resend-invite action. For PM confirmation.",
 "deviation"),

("DEV-SET-05","SETTINGS - COMPANY / Plans|11",
 "No image upload in the company's Add New Plan modal",
 "Low","P4",
 "The company Add New Plan modal is a two-step plan picker (Step 1 lists existing plans, Step 2 captures the Plan Code) and contains 0 file inputs. "
 "The test case expects a profile image section. For PM confirmation.",
 "deviation"),

("OBS-SET-01","All grids / Add Filter scenarios",
 "Saved 'Custom Filter' tabs created by Add Filter cannot be removed from the UI",
 "Low","P4",
 "Every execution of an 'Add Filter' scenario permanently adds a 'Custom Filter' tab to that grid for the logged-in user. The tabs are rendered as "
 "<li class='dnaTable2-headerSet-item'><a data-setindex=N> with no close/remove affordance anywhere in the UI, so they accumulate (12+ observed on some grids) "
 "and cannot be cleaned up. Noted as run residue on the agentqa account.",
 "observation"),
]

wb=openpyxl.load_workbook(resultio.F)
ws=wb["DEFECT LOG"]
# clear existing rows below the header
for r in range(2, ws.max_row+1):
    for c in range(1, 14): ws.cell(r,c).value=None
row=2
for did,linked,summary,sev,pri,steps,kind in DEFECTS:
    status = "Open" if kind=="bug" else ("For PM confirmation" if kind=="deviation" else "Noted")
    ws.cell(row,1).value=did
    ws.cell(row,2).value=linked
    ws.cell(row,3).value=summary
    ws.cell(row,4).value=sev
    ws.cell(row,5).value=pri
    ws.cell(row,6).value=status
    ws.cell(row,7).value=steps
    ws.cell(row,8).value=ENV
    ws.cell(row,9).value=BY
    ws.cell(row,10).value=D
    ws.cell(row,11).value="Unassigned"
    row+=1
wb.save(resultio.F)
bugs=[d for d in DEFECTS if d[6]=="bug"]
devs=[d for d in DEFECTS if d[6]=="deviation"]
obs=[d for d in DEFECTS if d[6]=="observation"]
print(f"wrote {len(DEFECTS)} defect-log rows: {len(bugs)} bugs, {len(devs)} deviations, {len(obs)} observations")
for d in bugs: print("  BUG:", d[0], d[3], "-", d[2][:70])
