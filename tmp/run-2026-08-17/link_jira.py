import sys, openpyxl
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio

MAP={
 "DEF-SET-01":"INSTA-1401","DEF-SET-09":"INSTA-1402","DEF-SET-10":"INSTA-1403",
 "DEF-CLAIM-01":"INSTA-1404","DEF-REG-01":"INSTA-1405","DEF-SET-03":"INSTA-1406",
 "DEF-SET-05":"INSTA-1407","DEF-SET-02":"INSTA-1408","DEF-USERS-01":"INSTA-1409",
}
wb=openpyxl.load_workbook(resultio.F)
# 1) scenario rows: append the Jira key to the Defect ID cell
n=0
for t in wb.sheetnames:
    if t in ("READ ME","SUMMARY","DEFECT LOG"): continue
    ws=wb[t]
    for r in range(2, ws.max_row+1):
        v=str(ws.cell(r,7).value or "")
        for did,key in MAP.items():
            if v.strip()==did:
                ws.cell(r,7).value=f"{did} / {key}"; n+=1
print("scenario rows linked:", n)
# 2) defect log: add a Jira column
ws=wb["DEFECT LOG"]
ws.cell(1,12).value="Jira issue"
m=0
for r in range(2, ws.max_row+1):
    did=str(ws.cell(r,1).value or "")
    if did in MAP:
        ws.cell(r,12).value=MAP[did]; m+=1
    elif did.startswith(("DEV-","OBS-")):
        ws.cell(r,12).value="not filed — reported for PM confirmation"
print("defect-log rows linked:", m)
wb.save(resultio.F)
