import sys, openpyxl, html
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio
def esc(x): return html.escape(str(x if x is not None else "")).replace("\n"," ")
def clip(x,n):
    t=" ".join(str(x if x is not None else "").split())
    return (t[:n].rstrip()+" …") if len(t)>n else t
def loz(s):
    c={"PASS":"green","FAIL":"red","BLOCKED":"yellow","N/A":"neutral"}.get(s,"neutral")
    return '<span data-type="status" data-color="%s">%s</span>'%(c,s)
GROUPS={
 "p4a":["SETTINGS - DEVICE  CATEGORY","SETTINGS - PRODUCT CATEGORY ","SETTINGS - REGISTRATION SURVEY "],
 "p4b":["SETTINGS - BRAND","SETTINGS - PLAN "],
 "p5a":["SETTINGS - REPAIR NETWORk ","SETTINGS - LANGUAGE","SETTINGS - REGIONS","SETTINGS - ADMINISTRATORS","SETTINGS - UNDERWRITERS"],
 "p5b":["SETTINGS - SUPPORT","SETTINGS - COVERAGE TYPE ","SETTINGS - COVERAGE COST TYPE ","SETTINGS - SHARE","SETTINGS-REVIEW QUESTIONS"],
}
for key,mods in GROUPS.items():
    P=['<div data-type="panel-info"><p>Full per-scenario results for this group, part of <strong>Instaprotek Regression Report — NULLNET-2026-08-17</strong>. Expected and actual result are recorded for every scenario; long text is abbreviated here and held unabridged in the run workbook.</p></div>']
    for m in mods:
        w,ws,idx=resultio.load(m)
        rows=[];sec=None;c={}
        for r in range(2,ws.max_row+1):
            a=ws.cell(r,1).value;b=ws.cell(r,2).value
            if a and str(a).strip(): sec=str(a).strip()
            if b is None: continue
            try: sid=int(float(str(b).strip()))
            except: continue
            st=str(ws.cell(r,6).value or "NOT RUN").upper().strip(); c[st]=c.get(st,0)+1
            rows.append((sec,sid,ws.cell(r,3).value,ws.cell(r,4).value,ws.cell(r,5).value,st,ws.cell(r,7).value))
        P.append('<h2>%s</h2><p><span data-type="status" data-color="blue">%d scenarios</span> &nbsp; %s</p>'
                 % (esc(m.strip()),len(rows)," · ".join("%s: %d"%(k.title(),v) for k,v in sorted(c.items()))))
        P.append('<table data-layout="full-width"><tbody><tr><th>Section</th><th>ID</th><th>Test</th><th>Expected</th><th>Actual</th><th>Status</th><th>Defect</th></tr>')
        for sec_,sid,desc,exp,act,st,dfx in rows:
            P.append("<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                     % (esc(sec_),sid,esc(clip(desc,85)),esc(clip(exp,130)),esc(clip(act,260)),loz(st),esc(clip(dfx,40))))
        P.append("</tbody></table>")
    b="".join(P)
    open(f"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/pages/{key}_compact.html","w").write(b)
    print(f"{key}: {len(b)/1024:.1f} KB  ({sum(1 for _ in mods)} modules)")
