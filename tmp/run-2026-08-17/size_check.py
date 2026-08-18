import sys, openpyxl, html
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
wb=openpyxl.load_workbook(resultio.F)
SKIP=("READ ME","SUMMARY","DEFECT LOG")
def esc(x): return html.escape(str(x if x is not None else "")).replace("\n","<br/>")
tot=0
for t in wb.sheetnames:
    if t in SKIP: continue
    w,ws,idx=resultio.load(t)
    size=0; n=0
    for r in range(2, ws.max_row+1):
        if ws.cell(r,2).value is None: continue
        n+=1
        size+=sum(len(esc(ws.cell(r,c).value)) for c in (1,3,4,5,7))+120
    tot+=size
    print(f"{t.strip():34s} {n:4d} rows  ~{size/1024:6.1f} KB")
print(f"TOTAL ~{tot/1024:.1f} KB")
