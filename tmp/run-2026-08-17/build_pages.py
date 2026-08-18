"""Build the Confluence parent report + grouped child pages (full per-scenario detail)."""
import sys, openpyxl, html, json, os
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio

wb=openpyxl.load_workbook(resultio.F)
SKIP=("READ ME","SUMMARY","DEFECT LOG")
OUT_OF_SCOPE=("ORDERS","PRODUCT REVIEWS","DEVICE BUYBACK")
OUT="/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/pages"
os.makedirs(OUT, exist_ok=True)

def esc(x): return html.escape(str(x if x is not None else "")).replace("\n","<br/>")
def loz(s):
    s=(s or "").upper()
    c={"PASS":"green","FAIL":"red","BLOCKED":"yellow","N/A":"neutral","NOT RUN":"neutral"}.get(s,"neutral")
    return '<span data-type="status" data-color="%s">%s</span>' % (c, esc(s))

tabs=[t for t in wb.sheetnames if t not in SKIP]
tot={}; per_module=[]; rows_by_tab={}
for t in tabs:
    w,ws,idx=resultio.load(t)
    c={}; rows=[]; sec=None
    for r in range(2, ws.max_row+1):
        a=ws.cell(r,1).value; b=ws.cell(r,2).value
        if a and str(a).strip(): sec=str(a).strip()
        if b is None: continue
        try: sid=int(float(str(b).strip()))
        except: continue
        st=str(ws.cell(r,6).value or "NOT RUN").upper().strip()
        c[st]=c.get(st,0)+1; tot[st]=tot.get(st,0)+1
        rows.append(dict(section=sec,sid=sid,desc=ws.cell(r,3).value,exp=ws.cell(r,4).value,
                         act=ws.cell(r,5).value,status=st,defect=ws.cell(r,7).value))
    rows_by_tab[t]=rows; per_module.append((t.strip(),len(rows),c))
TOTAL=sum(len(r) for r in rows_by_tab.values())
executed=tot.get("PASS",0)+tot.get("FAIL",0)
rate=100*tot.get("PASS",0)/executed if executed else 0

def module_section(t):
    rows=rows_by_tab[t]; c={}
    for row in rows: c[row["status"]]=c.get(row["status"],0)+1
    P=[]
    P.append('<h2>%s</h2>' % esc(t.strip()))
    P.append('<p><span data-type="status" data-color="blue">%d scenarios</span> &nbsp; %s</p>'
             % (len(rows), " · ".join("%s: %d"%(k.title(),v) for k,v in sorted(c.items()))))
    if t.strip() in OUT_OF_SCOPE:
        P.append('<p><em>Out of scope for the portal regression suite (app-only module). All scenarios recorded N/A and excluded from the pass rate.</em></p>')
    P.append('<table data-layout="full-width"><tbody><tr><th>Section</th><th>ID</th><th>Test description</th>'
             '<th>Expected result</th><th>Actual result</th><th>Status</th><th>Notes / Defect ID</th></tr>')
    def clip(x, n):
        t=str(x if x is not None else "").strip()
        t=" ".join(t.split())
        return (t[:n].rstrip()+" …") if len(t)>n else t
    for row in rows:
        P.append("<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (esc(row["section"]),row["sid"],esc(clip(row["desc"],110)),esc(clip(row["exp"],200)),
                    esc(clip(row["act"],420)),loz(row["status"]),esc(row["defect"])))
    P.append("</tbody></table>")
    return "".join(P)

# ---------- group children so each stays comfortably under ~70KB ----------
GROUPS=[
 ("Detailed results 1 — Users, Registration, Repair Shops",
  ["USERS","PORTAL - REGISTRATION","REPAIR SHOPS"]),
 ("Detailed results 2 — Affiliates, Claim Reports",
  ["AFFILIATES","CLAIM REPORTS"]),
 ("Detailed results 3 — Settings: Company",
  ["SETTINGS - COMPANY "]),
 ("Detailed results 4 — Settings: Device Category, Product Category, Brand, Plan, Registration Survey",
  ["SETTINGS - DEVICE  CATEGORY","SETTINGS - PRODUCT CATEGORY ","SETTINGS - BRAND","SETTINGS - PLAN ","SETTINGS - REGISTRATION SURVEY "]),
 ("Detailed results 5 — Settings: remaining tabs",
  ["SETTINGS - REPAIR NETWORk ","SETTINGS - LANGUAGE","SETTINGS - REGIONS","SETTINGS - ADMINISTRATORS",
   "SETTINGS - UNDERWRITERS","SETTINGS - SUPPORT","SETTINGS - COVERAGE TYPE ","SETTINGS - COVERAGE COST TYPE ",
   "SETTINGS - SHARE","SETTINGS-REVIEW QUESTIONS"]),
 ("Detailed results 6 — Out-of-scope modules (N/A)",
  ["ORDERS","PRODUCT REVIEWS","DEVICE BUYBACK"]),
]
manifest=[]
seen=set()
for i,(title,mods) in enumerate(GROUPS,1):
    body=['<div data-type="panel-info"><p>Full per-scenario results for this group, part of '
          '<strong>Instaprotek Regression Report — NULLNET-2026-08-17</strong>. '
          'Every scenario is listed with its expected and actual result.</p></div>']
    for m in mods:
        if m not in rows_by_tab:
            raise SystemExit("unknown tab %r" % m)
        seen.add(m); body.append(module_section(m))
    b="".join(body)
    fn="%s/child%d.html" % (OUT,i)
    open(fn,"w").write(b)
    manifest.append({"title":title,"file":fn,"kb":round(len(b)/1024,1),"modules":mods})
    print(f"child{i}: {len(b)/1024:6.1f} KB  {title}")

missing=[t for t in tabs if t not in seen]
if missing: raise SystemExit("modules not assigned to a child page: %r" % missing)

# ---------- parent ----------
P=[]; A=P.append
A('<div data-type="panel-info">'
  '<p><strong>Environment note.</strong> This cycle ran against <code>crm.nullnet.instaprotek.com</code> at the PM&#39;s direction, '
  'not the usual QA environment. That host carries <strong>live production data</strong> — 1,263,184 registrations and 123,115 claims at the '
  'start of the run, with the counters incrementing during the session and the day&#39;s registrations showing real customer names, personal '
  'email addresses, mobile numbers and IMEIs. Execution was constrained accordingly: scenarios that would have created, altered or deleted a '
  'real customer record, or emailed a real customer, were deliberately not executed and are recorded as <em>Blocked</em> with that reason. '
  'Every record created for this run was a self-created test fixture.</p></div>')

A("<h2>Run metadata</h2><table><tbody>")
for k,v in [("Run tag","NULLNET-2026-08-17"),
            ("Environment","<code>https://crm.nullnet.instaprotek.com</code> — live production data (not QA)"),
            ("Run date","2026-08-17"),
            ("Tester / account","Automated regression run, <code>agentqa@dnamicro.com</code> (Agent role — single login available)"),
            ("Suite source","<code>Insta-testing/Regression_QA_Log_NULLNET-2026-08-17.xlsx</code>"),
            ("Scenarios","%d across %d module tabs" % (TOTAL,len(tabs))),
            ("Browser","Chromium (Playwright, headless)")]:
    A("<tr><th>%s</th><td>%s</td></tr>" % (k,v))
A("</tbody></table>")

A("<h2>Run summary</h2>")
A("<table><tbody><tr><th>Total</th><th>Pass</th><th>Fail</th><th>Blocked</th><th>N/A (out of scope)</th><th>Executed</th><th>Pass rate</th></tr>")
A("<tr><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td><strong>%.1f%%</strong></td></tr>"
  % (TOTAL,tot.get("PASS",0),tot.get("FAIL",0),tot.get("BLOCKED",0),tot.get("N/A",0),executed,rate))
A("</tbody></table>")
A("<p>Pass rate is measured over executed scenarios (Pass + Fail). Out-of-scope modules are excluded per the suite&#39;s scope note; "
  "Blocked scenarios are excluded because they were not executed.</p>")

A("<h2>Per-module roll-up</h2>")
A("<table><tbody><tr><th>Module</th><th>Scenarios</th><th>Pass</th><th>Fail</th><th>Blocked</th><th>N/A</th><th>Pass rate (executed)</th></tr>")
for name,n,c in per_module:
    ex=c.get("PASS",0)+c.get("FAIL",0)
    pr=("%.0f%%"%(100*c.get("PASS",0)/ex)) if ex else "—"
    A("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td></tr>"
      % (esc(name),n,c.get("PASS",0),c.get("FAIL",0),c.get("BLOCKED",0),c.get("N/A",0),pr))
A("</tbody></table>")

A("<h2>Defects</h2>")
A("<p>Nine genuine product defects were filed as Jira Bugs in project <strong>INSTA</strong>, label <code>regression</code>, left "
  "<strong>Unassigned</strong>, in sprint id <strong>5590</strong> — the sprint holding the previous cycle&#39;s regression bug (INSTA-1398). "
  "<strong>Note for the PM:</strong> that sprint has been renamed from &quot;Regression Testing Bugs&quot; to &quot;Sprint 1&quot;, so no sprint "
  "matching the documented name exists any more. Please confirm this is still the intended destination.</p>")
A("<p>A further eight findings are recorded as <em>deviations</em> — fields or tabs the test cases describe that simply do not exist on this "
  "build. They look like the suite lagging behind a redesign rather than regressions, so they were <strong>not</strong> filed as bugs and are "
  "flagged here for PM confirmation.</p>")
ws=wb["DEFECT LOG"]
A("<table data-layout=\"full-width\"><tbody><tr><th>ID</th><th>Jira</th><th>Module / scenario</th><th>Summary</th><th>Severity</th><th>Priority</th><th>Status</th></tr>")
for r in range(2, ws.max_row+1):
    did=ws.cell(r,1).value
    if not did: continue
    j=str(ws.cell(r,12).value or "")
    jc=('<a href="https://dnamicro.atlassian.net/browse/%s">%s</a>'%(j,j)) if j.startswith("INSTA-") else esc(j)
    A("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
      % (esc(did),jc,esc(ws.cell(r,2).value),esc(ws.cell(r,3).value),
         esc(ws.cell(r,4).value),esc(ws.cell(r,5).value),esc(ws.cell(r,6).value)))
A("</tbody></table>")
A("<p>Full reproduction steps for each bug are in the linked Jira issue; for the deviations and the observation they are in the "
  "<strong>DEFECT LOG</strong> tab of the run workbook.</p>")

A("<h2>Blocked scenarios and why</h2>")
A("<p>All %d blocked scenarios, each with the reason it was not executed.</p>" % tot.get("BLOCKED",0))
A('<table data-layout="full-width"><tbody><tr><th>Module</th><th>Scenario</th><th>Test</th><th>Reason not executed</th></tr>')
for t in tabs:
    for row in rows_by_tab[t]:
        if row["status"]=="BLOCKED":
            A("<tr><td>%s</td><td>%s|%d</td><td>%s</td><td>%s</td></tr>"
              % (esc(t.strip()),esc(row["section"]),row["sid"],esc(row["desc"]),esc(row["act"])))
A("</tbody></table>")

A("<h2>Full per-scenario results</h2>")
A("<p>Every scenario in the suite, with expected and actual result recorded for each, is published across the child pages below. "
  "They are split only for page size — together they cover all %d scenarios.</p>" % TOTAL)
A("<p><em>Child pages are listed under this page in the page tree.</em></p>")
A("<ul>")
for m in manifest:
    A("<li><strong>%s</strong> — %s</li>" % (esc(m["title"]), esc(", ".join(x.strip() for x in m["modules"]))))
A("</ul>")

A("<h2>Release readiness — Go / No-go</h2>")
A("<table><tbody><tr><th>Exit criterion</th><th>Result</th><th>Assessment</th></tr>")
A("<tr><td>All selected scenarios executed</td><td>%d executed, %d blocked</td>"
  "<td>Partially met — every blocked item is documented, and most were blocked by a deliberate safety decision on a live-data environment rather than by product failure.</td></tr>"
  % (executed,tot.get("BLOCKED",0)))
A("<tr><td>No open Critical/High defects</td><td>0 Critical, <strong>2 High</strong> (INSTA-1401, INSTA-1402)</td><td><strong>Not met.</strong></td></tr>")
A("<tr><td>Pass rate ≥ 95%%</td><td>%.1f%%</td><td>Met.</td></tr>" % rate)
A("<tr><td>Tracker and defect log updated</td><td>Yes</td><td>Met.</td></tr>")
A("<tr><td>PM sign-off</td><td>Pending</td><td>Outstanding.</td></tr>")
A("</tbody></table>")

A('<div data-type="panel-warning">'
  '<p><strong>Recommendation: NO-GO pending the two High defects.</strong> The pass rate clears the 95%% gate comfortably '
  '(%.1f%% of executed scenarios) and the great majority of the portal behaves correctly, but two High-severity defects are open:</p>'
  '<ul>'
  '<li><strong>INSTA-1401</strong> — the Languages settings filter crashes the entire page to a blank screen, on every filter column.</li>'
  '<li><strong>INSTA-1402</strong> — company delete and plan removal both fail with HTTP 400 and surface no error; with INSTA-1403 '
  '(the Status selector will not apply Inactive) there is currently no way to delete or deactivate a company.</li>'
  '</ul>'
  '<p>Neither sits on the highest-traffic customer path. If the business accepts them as known issues with a documented workaround this '
  'becomes a conditional GO — that is a PM call.</p></div>' % rate)

A("<h2>Notes and caveats</h2><ul>"
  "<li><strong>Single login.</strong> Only the Agent-role account was available, so role-permission scenarios could not be differentiated.</li>"
  "<li><strong>Deliberate non-execution.</strong> Creating a claim against a real customer&#39;s registration, sending the customer-facing "
  "claim email, and replacing a real customer&#39;s stored receipt were all left unexecuted by choice on a production-data environment.</li>"
  "<li><strong>Test data.</strong> Records created for this run were named <code>RegressionTest0817</code> (or similar) and deleted afterwards, "
  "with one exception below.</li>"
  "<li><strong>Residue needing manual cleanup.</strong> One test company, <code>RegressionTest0817</code>, could not be removed: delete returns "
  "HTTP 400 (INSTA-1402) and Status will not change to Inactive (INSTA-1403). Its child product and batch were deleted; one attached plan could "
  "not be detached for the same reason. It needs manual removal once those defects are fixed.</li>"
  "<li><strong>Saved filter tabs.</strong> Every &quot;Add Filter&quot; scenario permanently adds a &quot;Custom Filter&quot; tab to that grid "
  "for the logged-in account and the UI offers no way to delete them (OBS-SET-01). Several accumulated on the agentqa account.</li>"
  "<li><strong>Verification approach.</strong> Automated failures were re-verified before being reported. A number of apparent failures proved "
  "to be harness or data-ordering artifacts (empty grids checked before data was created, role-conditional fields, widgets needing keyboard "
  "activation) and were corrected rather than filed — for example the User contact fields render only for the Basic Client role, and the "
  "expired-plan guard on the claim wizard is correct behaviour, not a defect.</li>"
  "</ul>")

body="".join(P)
open(OUT+"/parent.html","w").write(body)
json.dump(manifest, open(OUT+"/manifest.json","w"), indent=1)
print("parent: %.1f KB" % (len(body)/1024))
print("TOTAL scenarios covered:", TOTAL)
