"""Classify each scenario BROWSE vs WRITE, section-aware.

Section context beats wording: every step inside a "New <entity>" section is part of a
create flow even when the step itself reads like a click. Grid 1-10 are display/filter/
search/export/open; Grid 11+ are edit/save/delete/confirm."""
import sys, re, json; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, openpyxl

WRITE_WORD = re.compile(r"\b(new|create|add|input|enter|type|upload|save|update|edit|delete|"
                        r"remove|check|uncheck|tick|submit|transfer|resend|assign|deactivate|"
                        r"activate|attach|replace|change password|reimburse|approve|deny|reject)\b", re.I)
# filter / search / export are read-only however they are worded ("Add Filter" is not a write)
FILTER_SAFE = re.compile(r"(add filter|select a filter|select a value|filter |filters\b|"
                         r"\bsearch\b|\bexport\b|sort|column|pagination|rows per page)", re.I)
PURE_VIEW  = re.compile(r"^\s*verify if .*(displayed|display|working|shown|listed|default|enabled|"
                        r"disabled|present|routes?)\b", re.I)

def classify(section, sid, desc, exp):
    s=(section or "").strip().lower()
    # read-only grid affordances always browse, whatever verbs appear
    if FILTER_SAFE.search(desc) and not re.search(r"\b(save|delete|create|upload|new button)\b", desc, re.I):
        return "BROWSE"
    # 1. anything inside a create section is a write flow, whatever the step says
    if s.startswith("new ") or s in ("support",):
        return "WRITE"
    # 2. notes sections create and edit notes
    if s == "notes":
        return "BROWSE" if PURE_VIEW.match(desc) and not WRITE_WORD.search(desc) else "WRITE"
    # 3. grid: 1-10 browse (display/filter/search/export/open), 11+ write (edit/save/delete/confirm)
    if s == "grid":
        # sheets differ: most put CRUD at 11+, but some (Registration Survey) pack
        # edit/save/delete into 1-7. Trust the verb over the position.
        if sid > 10: return "WRITE"
        # a bare "Click Yes/No button" is the confirm step of a delete flow: judge it
        # by its EXPECTED RESULT, and by the fact it is unreachable without the delete.
        if re.search(r"\b(yes|no) button\b", desc, re.I): return "WRITE"
        if WRITE_WORD.search(desc) and not PURE_VIEW.match(desc): return "WRITE"
        if WRITE_WORD.search(exp) and not PURE_VIEW.match(desc): return "WRITE"
        return "BROWSE"
    # 4. timeline is read-only by nature
    if s == "timeline":
        return "BROWSE"
    # 5. everything else: pure view assertions browse, action verbs write
    if PURE_VIEW.match(desc) and not WRITE_WORD.search(desc):
        return "BROWSE"
    if WRITE_WORD.search(desc) or WRITE_WORD.search(exp):
        return "WRITE"
    return "BROWSE"

wb=openpyxl.load_workbook(resultio.F)
out={}; tot={"BROWSE":0,"WRITE":0}
for tab in wb.sheetnames:
    if tab in ("READ ME","SUMMARY","DEFECT LOG"): continue
    ws=wb[tab]; _,_,idx=resultio.load(tab)
    for k,r in idx.items():
        sec,sid = k.rsplit("|",1); sid=int(sid)
        c=classify(sec, sid, str(ws.cell(r,3).value or ""), str(ws.cell(r,4).value or ""))
        out.setdefault(tab,{})[k]=c; tot[c]+=1
json.dump(out, open("/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/classification.json","w"), indent=1)
print("TOTALS:", tot)
