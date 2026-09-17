"""Apply the Production scope rule from the updated SKILL.md.

Write cases outside Registration + Claim Reports become N/A. Where a result already
exists from the 2026-09-16 execution, the observation is preserved in the note so no
evidence is lost."""
import sys, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, openpyxl
IN_SCOPE={"PORTAL - REGISTRATION","CLAIM REPORTS"}
FULLY_NA={"ORDERS","PRODUCT REVIEWS","DEVICE BUYBACK"}
NOTE="Production run — create/edit/delete out of scope"
cls=json.load(open("/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/classification.json"))
wb=openpyxl.load_workbook(resultio.F)
changed=0; preserved=0; report={}
for tab in wb.sheetnames:
    if tab in ("READ ME","SUMMARY","DEFECT LOG"): continue
    if tab.strip() in FULLY_NA: continue
    ws=wb[tab]; _,_,idx=resultio.load(tab)
    n=0
    for k,r in idx.items():
        if cls.get(tab,{}).get(k)!="WRITE": continue
        if tab.strip() in IN_SCOPE: continue
        prev_st=str(ws.cell(r,5).value or "").strip()
        prev_nt=str(ws.cell(r,6).value or "").strip()
        note=NOTE
        if prev_st and prev_st not in ("Not Tested","N/A"):
            note=f"{NOTE}. [Executed 2026-09-16 before the scope change — result was {prev_st}: {prev_nt}]"
            preserved+=1
        ws.cell(r,5).value="N/A"
        ws.cell(r,6).value=note[:900]
        ws.cell(r,7).value="None"
        changed+=1; n+=1
    if n: report[tab]=n
wb.save(resultio.F)
print(f"set N/A: {changed}  (of which preserved a prior observation: {preserved})")
for t,n in report.items(): print(f"   {t:34s} {n}")
