import sys, openpyxl, html, json
sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-08-17")
import resultio

wb=openpyxl.load_workbook(resultio.F)
SKIP=("READ ME","SUMMARY","DEFECT LOG")
OUT_OF_SCOPE=("ORDERS","PRODUCT REVIEWS","DEVICE BUYBACK")

def esc(x): return html.escape(str(x if x is not None else "")).replace("\n","<br/>")

def lozenge(status):
    s=(status or "").upper()
    colour={"PASS":"green","FAIL":"red","BLOCKED":"yellow","N/A":"neutral","NOT RUN":"neutral"}.get(s,"neutral")
    return '<span data-type="status" data-color="%s">%s</span>' % (colour, esc(s))

# ---------- gather ----------
tabs=[t for t in wb.sheetnames if t not in SKIP]
tot={}; per_module=[]; rows_by_tab={}
for t in tabs:
    w,ws,idx=resultio.load(t)
    c={}; rows=[]
    sec=None
    for r in range(2, ws.max_row+1):
        a=ws.cell(r,1).value; b=ws.cell(r,2).value
        if a and str(a).strip(): sec=str(a).strip()
        if b is None: continue
        try: sid=int(float(str(b).strip()))
        except: continue
        st=str(ws.cell(r,6).value or "NOT RUN").upper().strip()
        c[st]=c.get(st,0)+1; tot[st]=tot.get(st,0)+1
        rows.append(dict(section=sec, sid=sid,
                         desc=ws.cell(r,3).value, exp=ws.cell(r,4).value,
                         act=ws.cell(r,5).value, status=st, defect=ws.cell(r,7).value))
    rows_by_tab[t]=rows
    per_module.append((t.strip(), len(rows), c))

executed=tot.get("PASS",0)+tot.get("FAIL",0)
rate=100*tot.get("PASS",0)/executed if executed else 0

P=[]
A=P.append

A('<div data-type="panel-info">'
  '<p><strong>Environment note.</strong> This cycle ran against <code>crm.nullnet.instaprotek.com</code> at the PM\'s direction, '
  'not the usual QA environment. That host carries <strong>live production data</strong> — 1,263,184 registrations and 123,115 claims at the '
  'start of the run, with the counters incrementing during the session and today\'s registrations showing real customer names, personal email '
  'addresses, mobile numbers and IMEIs. Test execution was therefore constrained: scenarios that would have created, altered or deleted real '
  'customer records, or emailed a real customer, were deliberately not executed and are recorded as <em>Blocked</em> with the reason. '
  'All records created for this run were self-created test fixtures.</p>'
  '</div>')

# ---------- run metadata ----------
A("<h2>Run metadata</h2>")
A("<table><tbody>")
for k,v in [
  ("Run tag","NULLNET-2026-08-17"),
  ("Environment","<code>https://crm.nullnet.instaprotek.com</code> — live production data (not QA)"),
  ("Run date","2026-08-17"),
  ("Tester / account","Automated regression run, <code>agentqa@dnamicro.com</code> (Agent role, single login)"),
  ("Suite source","<code>Insta-testing/Regression_QA_Log_NULLNET-2026-08-17.xlsx</code> (copy of Instaprotek_Regression_QA_Log.xlsx)"),
  ("Scenarios in suite","%d across %d module tabs" % (sum(len(r) for r in rows_by_tab.values()), len(tabs))),
  ("Browser","Chromium (Playwright, headless)"),
]:
    A("<tr><th>%s</th><td>%s</td></tr>" % (k,v))
A("</tbody></table>")

# ---------- summary ----------
A("<h2>Run summary</h2>")
A("<table><tbody><tr>"
  "<th>Total</th><th>Pass</th><th>Fail</th><th>Blocked</th><th>N/A (out of scope)</th><th>Executed</th><th>Pass rate</th></tr>")
A("<tr><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td><strong>%.1f%%</strong></td></tr>"
  % (sum(len(r) for r in rows_by_tab.values()), tot.get("PASS",0), tot.get("FAIL",0),
     tot.get("BLOCKED",0), tot.get("N/A",0), executed, rate))
A("</tbody></table>")
A("<p>Pass rate is measured over executed scenarios (Pass + Fail). Out-of-scope modules are excluded per the suite's scope note; "
  "Blocked scenarios are excluded because they were not executed.</p>")

# ---------- per-module roll-up ----------
A("<h2>Per-module roll-up</h2>")
A("<table><tbody><tr><th>Module</th><th>Scenarios</th><th>Pass</th><th>Fail</th><th>Blocked</th><th>N/A</th><th>Pass rate (executed)</th></tr>")
for name,n,c in per_module:
    ex=c.get("PASS",0)+c.get("FAIL",0)
    pr=("%.0f%%" % (100*c.get("PASS",0)/ex)) if ex else "—"
    A("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td></tr>"
      % (esc(name), n, c.get("PASS",0), c.get("FAIL",0), c.get("BLOCKED",0), c.get("N/A",0), pr))
A("</tbody></table>")

# ---------- defects ----------
A("<h2>Defects raised</h2>")
A("<p>Nine genuine product defects were filed as Jira Bugs in project INSTA, label <code>regression</code>, left Unassigned. "
  "They were placed in sprint id <strong>5590</strong> — the sprint that holds the previous cycle's regression bug (INSTA-1398). "
  "<strong>Note for the PM:</strong> that sprint has since been renamed from &quot;Regression Testing Bugs&quot; to &quot;Sprint 1&quot;, "
  "so no sprint matching the documented name exists any more. Please confirm this is still the intended destination.</p>")
ws=wb["DEFECT LOG"]
A("<table><tbody><tr><th>Defect ID</th><th>Jira</th><th>Module / scenario</th><th>Summary</th><th>Severity</th><th>Priority</th><th>Status</th></tr>")
for r in range(2, ws.max_row+1):
    did=ws.cell(r,1).value
    if not did: continue
    jira=str(ws.cell(r,12).value or "")
    jcell = ('<a href="https://dnamicro.atlassian.net/browse/%s">%s</a>' % (jira,jira)) if jira.startswith("INSTA-") else esc(jira)
    A("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
      % (esc(did), jcell, esc(ws.cell(r,2).value), esc(ws.cell(r,3).value),
         esc(ws.cell(r,4).value), esc(ws.cell(r,5).value), esc(ws.cell(r,6).value)))
A("</tbody></table>")

A("<h3>Reproduction detail</h3>")
for r in range(2, ws.max_row+1):
    did=ws.cell(r,1).value
    if not did: continue
    A("<p><strong>%s — %s</strong><br/>%s</p>" % (esc(did), esc(ws.cell(r,3).value), esc(ws.cell(r,7).value)))

# ---------- blocked ----------
A("<h2>Blocked and not-executed scenarios</h2>")
A("<p>Every blocked scenario is listed with the reason it was not executed.</p>")
A("<table><tbody><tr><th>Module</th><th>Scenario</th><th>Test</th><th>Reason not executed</th></tr>")
for t in tabs:
    for row in rows_by_tab[t]:
        if row["status"]=="BLOCKED":
            A("<tr><td>%s</td><td>%s|%d</td><td>%s</td><td>%s</td></tr>"
              % (esc(t.strip()), esc(row["section"]), row["sid"], esc(row["desc"]), esc(row["act"])))
A("</tbody></table>")

# ---------- full per-scenario results ----------
A("<h2>Full per-scenario results</h2>")
A("<p>Every scenario in the suite, grouped by module, with expected and actual result recorded for each.</p>")
for t in tabs:
    rows=rows_by_tab[t]
    c=dict()
    for row in rows: c[row["status"]]=c.get(row["status"],0)+1
    A('<h3>%s</h3><p><span data-type="status" data-color="blue">%d scenarios</span></p>'
      % (esc(t.strip()), len(rows)))
    if t.strip() in OUT_OF_SCOPE:
        A("<p><em>Out of scope for the portal regression suite (app-only module) — all scenarios recorded N/A and excluded from the pass rate.</em></p>")
    A("<p>" + " · ".join("%s: %d" % (k.title(),v) for k,v in sorted(c.items())) + "</p>")
    A('<table><tbody><tr><th>Section</th><th>ID</th><th>Test description</th><th>Expected result</th><th>Actual result</th><th>Status</th><th>Notes / Defect ID</th></tr>')
    for row in rows:
        A("<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
          % (esc(row["section"]), row["sid"], esc(row["desc"]), esc(row["exp"]),
             esc(row["act"]), lozenge(row["status"]), esc(row["defect"])))
    A("</tbody></table>")

# ---------- go / no-go ----------
A("<h2>Release readiness — Go / No-go</h2>")
A("<table><tbody><tr><th>Exit criterion</th><th>Result</th><th>Assessment</th></tr>")
A("<tr><td>All selected P1/P2 scenarios executed</td><td>%d of %d executed; %d blocked</td>"
  "<td>Partially met — every blocked item is documented, and the majority were blocked by a deliberate safety decision on a live-data environment rather than by product failure.</td></tr>"
  % (executed, executed+tot.get("BLOCKED",0), tot.get("BLOCKED",0)))
A("<tr><td>No open Critical/High defects</td><td>2 High open (INSTA-1401, INSTA-1402); 0 Critical</td>"
  "<td><strong>Not met.</strong></td></tr>")
A("<tr><td>Pass rate ≥ 95%%</td><td>%.1f%%</td><td>Met.</td></tr>" % rate)
A("<tr><td>Tracker and defect log updated</td><td>Yes</td><td>Met — workbook and this report.</td></tr>")
A("<tr><td>PM sign-off</td><td>Pending</td><td>Outstanding.</td></tr>")
A("</tbody></table>")

A('<div data-type="panel-warning">'
  '<p><strong>Recommendation: NO-GO pending the two High defects.</strong> The pass rate comfortably clears the 95%% gate '
  '(%.1f%% of executed scenarios), and the great majority of the portal behaves correctly. However two High-severity defects are open:</p>'
  '<ul>'
  '<li><strong>INSTA-1401</strong> — the Languages settings filter crashes the whole page to a blank screen on every filter column.</li>'
  '<li><strong>INSTA-1402</strong> — company delete and plan removal both fail with HTTP 400 and no error is surfaced to the user; '
  'combined with INSTA-1403 there is currently no way to delete or deactivate a company.</li>'
  '</ul>'
  '<p>Neither is on the highest-traffic customer path, so if the business accepts them as known issues with a documented workaround, '
  'this becomes a conditional GO. That is a PM call.</p>'
  '</div>' % rate)

A("<h2>Notes and caveats</h2>")
A("<ul>"
  "<li><strong>Single login.</strong> Only the Agent-role account was available, so role-permission scenarios could not be differentiated.</li>"
  "<li><strong>Deliberate non-execution.</strong> Creating a claim against a real customer's registration, sending the customer-facing claim "
  "email, and replacing a real customer's stored receipt were all left unexecuted by choice. Each is recorded as Blocked with that reason.</li>"
  "<li><strong>Test data.</strong> Every record created for this run was a self-created fixture named <code>RegressionTest0817</code> "
  "(or similar) and was deleted afterwards, with one exception below.</li>"
  "<li><strong>Residue.</strong> One test company, <code>RegressionTest0817</code>, could not be removed: company delete returns HTTP 400 "
  "(INSTA-1402) and the Status selector will not apply Inactive (INSTA-1403). It remains on the environment and needs manual removal once "
  "those defects are fixed. Its child product and batch were removed; one attached plan could not be detached for the same reason.</li>"
  "<li><strong>Saved filter tabs.</strong> Each execution of an &quot;Add Filter&quot; scenario permanently adds a &quot;Custom Filter&quot; "
  "tab to that grid for the logged-in account, and the UI offers no way to delete them (defect-log entry OBS-SET-01). Several accumulated on "
  "the agentqa account during this run.</li>"
  "<li><strong>Test-case drift.</strong> Eight findings are recorded as deviations rather than bugs — fields or tabs the test cases describe "
  "that do not exist on this build (Plan Type, Device Management System on company Details, Claim Summary / Claim Status Details tabs, the "
  "Problem Summary wizard step, receipt replace, resend-invite). These look like the suite lagging behind a redesign and need PM confirmation "
  "before anyone files them.</li>"
  "</ul>")

body="".join(P)
open("/home/farsheed/pm-instaprotek/tmp/run-2026-08-17/confluence_body.xml","w").write(body)
print("body length:", len(body))
print("scenarios:", sum(len(r) for r in rows_by_tab.values()))
print("totals:", tot, "executed", executed, "rate %.1f%%" % rate)
