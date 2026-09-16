import sys, json, os
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio
MAP={
 "coverage-cost-type":"SETTINGS - COVERAGE COST TYPE ",
 "coverage-type":"SETTINGS - COVERAGE TYPE ",
 "repair-network":"SETTINGS - REPAIR NETWORk ",
 "regions":"SETTINGS - REGIONS",
 "administrators":"SETTINGS - ADMINISTRATORS",
 "underwriters":"SETTINGS - UNDERWRITERS",
 "review-questions":"SETTINGS-REVIEW QUESTIONS",
 "languages":"SETTINGS - LANGUAGE",
 "share":"SETTINGS - SHARE",
 "support":"SETTINGS - SUPPORT",
}
NORM={"PASS":"Pass","FAIL":"Fail","PARTIAL":"Pass","BLOCKED":"Blocked","NA":"N/A","N/A":"N/A"}
EV="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/evidence/settings"
for key in sys.argv[1:]:
    tab=MAP[key]; f=f"{EV}/{key}/results.json"
    if not os.path.exists(f): print(f"{key}: no results.json"); continue
    R=json.load(open(f))
    res={}
    for k,(st,note) in R.items():
        s=NORM.get(st.upper(),st)
        if st.upper()=="PARTIAL": note="(partial) "+note
        res[k]=(s,note)
    n,missed,_=resultio.write(tab,res)
    print(f"{key:22s} -> {tab:32s} wrote {n}  missed={missed}")
    print("   tally:", resultio.tally(tab)[0])
