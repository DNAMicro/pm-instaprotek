"""Build the full Confluence report body: metadata, summary, per-module roll-up,
and EVERY scenario with expected vs actual."""
import sys, html, re; sys.path.insert(0,"/home/farsheed/pm-instaprotek/tmp/run-2026-09-16")
import resultio, openpyxl
LOZ={"Pass":("green","Pass"),"Fail":("red","Fail"),"Blocked":("yellow","Blocked"),
     "N/A":("grey","N/A"),"Not Tested":("grey","Not Tested")}
def loz(s):
    c,t=LOZ.get(s,("grey",s or "?"))
    return '<span data-type="status" data-color="%s">%s</span>'%(c.lower(), html.escape(t))
def e(x): return html.escape(str(x if x is not None else "")).replace("\n","<br/>")

wb=openpyxl.load_workbook(resultio.F)
g={}; rows=[]; per=[]
for t in wb.sheetnames:
    if t in ("READ ME","SUMMARY","DEFECT LOG"): continue
    ws=wb[t]; _,_,idx=resultio.load(t); c,n=resultio.tally(t)
    for k,v in c.items(): g[k]=g.get(k,0)+v
    per.append((t,n,c))
    for k,r in idx.items():
        rows.append((t,k,str(ws.cell(r,3).value or ""),str(ws.cell(r,4).value or ""),
                     str(ws.cell(r,5).value or "").strip(),str(ws.cell(r,6).value or ""),
                     str(ws.cell(r,7).value or "None")))
ex=g.get("Pass",0)+g.get("Fail",0)+g.get("Blocked",0); att=g.get("Pass",0)+g.get("Fail",0)

P=[]
P.append('<div data-type="panel-warning"><p><strong>This run deleted a live '
 'Production record.</strong> Product plan <code>d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a</code> '
 '("2 - Years Warranty Replacement") was deleted by the test harness on 2026-09-16 at 11:53 MST. It is not '
 'recoverable through the portal and needs a database restore. 289 registrations reference it. See the Incident '
 'section below.</p></div>')
P.append("<h2>Run metadata</h2><table><tbody>")
for k,v in [("Version","PROD-2026-09-16"),("Environment","Production — https://crm.instaprotek.com"),
   ("Run dates","2026-09-16 to 2026-09-17"),("Tester account","agentqa@dnamicro.com (Agent role)"),
   ("Suite source","Insta-testing/Regression_QA_Log_PROD-2026-09-16.xlsx (979 scenarios, 24 module tabs)"),
   ("Scope","Production scope per SKILL.md: Registration and Claims in full, browse-only smoke checks elsewhere, no other record creation"),
   ("Harness","Playwright (pipx) headless Chromium")]:
    P.append(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>")
P.append("</tbody></table>")

P.append("<h2>Run summary</h2><table><tbody>")
P.append(f"<tr><th>Total scenarios</th><td>979</td></tr>")
for s in ["Pass","Fail","Blocked","N/A"]:
    P.append(f"<tr><th>{s}</th><td>{g.get(s,0)}</td></tr>")
P.append(f"<tr><th>Executed (Pass+Fail+Blocked)</th><td>{ex}</td></tr>")
P.append(f"<tr><th>Attempted (Pass+Fail)</th><td>{att}</td></tr>")
P.append(f"<tr><th>Pass rate of attempted</th><td><strong>{g.get('Pass',0)/att*100:.1f}%</strong></td></tr>")
P.append("</tbody></table>")
P.append('<div data-type="panel-info"><p><strong>Read the pass rate carefully.</strong> '
 '99.5% of <em>attempted</em> scenarios passed, but only 210 of 979 were attempted. 519 are N/A (PM-excluded modules '
 'plus create/edit/delete cases barred on Production) and 250 are Blocked. This run verifies that Production '
 '<em>renders and navigates</em>; it does not verify that create, edit and delete flows work. '
 '<strong>It is not a substitute for a QA or Staging regression, and should not be used alone as a release gate.</strong>'
 '</p></div>')

P.append("<h2>Per-module roll-up</h2><table><tbody><tr><th>Module</th><th>Total</th><th>Pass</th><th>Fail</th><th>Blocked</th><th>N/A</th></tr>")
for t,n,c in per:
    P.append(f"<tr><td>{e(t.strip())}</td><td>{n}</td><td>{c.get('Pass',0)}</td><td>{c.get('Fail',0)}</td>"
             f"<td>{c.get('Blocked',0)}</td><td>{c.get('N/A',0)}</td></tr>")
P.append("</tbody></table>")

P.append("<h2>Defect log</h2><table><tbody><tr><th>Defect</th><th>Module / case</th><th>Severity</th><th>Priority</th>"
 "<th>Status</th><th>Repro</th><th>Environment</th></tr>")
P.append("<tr><td>INSTA-1401 (existing — Production recurrence recorded as a comment, not re-filed)</td>"
 "<td>Settings &gt; Languages — SETTINGS - LANGUAGE / Grid|4</td><td>High</td><td>High</td><td>To Do, Sprint 2</td>"
 "<td>Settings &gt; Languages &rarr; Filter Languages &rarr; Select a filter &rarr; choose any column. The page "
 "collapses: body innerText length 0, innerHTML 116 chars, nav and grid gone. Full reload required. Search, export "
 "and record-open all work on a fresh page, so the defect is isolated to the filter step.</td>"
 "<td>Production — crm.instaprotek.com</td></tr>")
P.append("</tbody></table>")
P.append("<p>No other defect was filed. 16 of the 17 first-pass failures were re-verified read-only and proved to be "
 "test-harness artifacts (slow Production page loads, a grid search that does not filter, and two build-shape "
 "differences), not product defects. Filing them unverified would have produced 16 false tickets.</p>")

P.append("<h2>Incident — live Production plan deleted</h2>")
P.append("<p>During the 2026-09-16 phase, the plan driver's teardown deleted a real Production product plan. Root "
 "cause was the harness, not the product: plan creation failed validation, the driver fell back to 'search the grid "
 "for our tag and open the first row', the Plans grid search does not filter, so it opened a real plan and deleted it.</p>")
P.append("<table><tbody>"
 "<tr><th>Record</th><td><code>d1dfbdbc-1cb0-48f5-aee9-5a5a4f594c3a</code></td></tr>"
 "<tr><th>Plan name</th><td>2 - Years Warranty Replacement</td></tr>"
 "<tr><th>Known fields</th><td>Region United States; Coverage Amount USD 9.16; Coverage Period 2; Terms PDF beginning 'Terms and Cond…'; had a profile image</td></tr>"
 "<tr><th>Unrecovered fields</th><td>Plan Code, SKU, Administrator, Underwriter, Support, Coverage Type, Coverage Cost Type, Coverage Type Amount, Channel</td></tr>"
 "<tr><th>Deleted at</th><td>2026-09-16 11:53 MST (18:53 UTC), logged in the portal Timeline as action 'Remove Company'</td></tr>"
 "<tr><th>Blast radius</th><td>289 registrations reference this plan. They still display the plan name and are not visibly broken; no new registration can be created against it, and anything resolving the plan by id at runtime may fail.</td></tr>"
 "<tr><th>Recovery</th><td>Not possible in-portal (hard delete; absent from CSV export; no Status filter; no archive view reachable at Agent role; the app's own grid API returns the same 53 plans for every status value). Requires a database restore from a backup before 2026-09-16 18:53 UTC, preserving the original id.</td></tr>"
 "<tr><th>Fix applied</th><td>Ownership guard added — every edit/save/delete now proves the open record carries the run tag, verified blocking a real record. The grid-search recovery path is removed. SKILL.md updated to bar plan CRUD on Production.</td></tr>"
 "</tbody></table>")

P.append("<h2>Blocked and skipped</h2><ul>"
 "<li><strong>Portal - Registration (41)</strong> — creating the shared test registration requires a Pincode tied to real product inventory; the kit supplies a barcode but no pincode. Not fabricated against live Production inventory, and no existing customer registration was used.</li>"
 "<li><strong>Claim Reports record cases (41)</strong> — claim filing is app-only and this run has no app access, so no test claim exists. Real customer claims were not edited.</li>"
 "<li><strong>Repair Shops, Affiliates, Product Category, Brand, Company sub-grids (≈166)</strong> — reachable only by creating or editing records, which the Production scope forbids.</li>"
 "<li><strong>Settings &gt; Review Questions Grid|10 (1)</strong> — row edit/delete render with DOM disabled=true for the Agent-role account. Verified against Coverage Type in the same session, where the same controls are enabled. Needs an Admin login to test.</li>"
 "</ul>")

P.append("<h2>Deviations for PM confirmation (not filed as bugs)</h2><ul>"
 "<li><strong>Claim Reports filter</strong> — selecting an identifier column (IMEI/Serial Number, Claim Number, Registration Number) shows a value control and enables Add Filter, but renders no 'Select a value' placeholder and offers no enumerable list, because these columns are free-text. Functionally correct; differs from the written expectation.</li>"
 "<li><strong>Plans grid search does not filter</strong> — searching a non-existent term returns all rows unfiltered. This is the proximate cause of the deletion incident and is worth a PM decision on whether to file it.</li>"
 "<li><strong>Registration Survey grid</strong> — renders its 3 questions but not with the standard table markup used by other grids.</li>"
 "</ul>")

P.append("<h2>Go / No-go</h2>")
P.append('<div data-type="panel-note"><p><strong>No recommendation is offered from this '
 'run.</strong> The exit gate requires all selected P1/P2 executed and a pass rate at or above target. Only 210 of 979 '
 'scenarios were attempted, so the gate cannot be evaluated. One open High defect (INSTA-1401) is confirmed on '
 'Production. A release decision needs a full QA or Staging regression; this Production pass can only confirm the '
 'portal renders and navigates.</p></div>')

PARENT="".join(P)
open("/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/parent_body.xml","w").write(PARENT)
print("parent bytes:", len(PARENT))

# per-module child bodies
import json, os
os.makedirs("/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/pages", exist_ok=True)
children={}
for t,n,c in per:
    B=[f"<p>Module <strong>{e(t.strip())}</strong> — {n} scenarios: {c.get('Pass',0)} Pass, {c.get('Fail',0)} Fail, "
       f"{c.get('Blocked',0)} Blocked, {c.get('N/A',0)} N/A. Part of the Instaprotek Regression Report PROD-2026-09-16.</p>"]
    B.append("<table><tbody><tr><th>Scenario</th><th>Test description</th><th>Expected result</th>"
             "<th>Actual result</th><th>Status</th><th>Notes / Defect</th></tr>")
    for rt,k,desc,exp,st,note,dfct in rows:
        if rt!=t: continue
        B.append(f"<tr><td>{e(k)}</td><td>{e(desc[:300])}</td><td>{e(exp[:300])}</td><td>{e(note[:700])}</td>"
                 f"<td>{loz(st)}</td><td>{e(dfct)}</td></tr>")
    B.append("</tbody></table>")
    body="".join(B)
    fn="/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/pages/"+re.sub(r"[^A-Za-z0-9]+","_",t.strip())+".xml"
    open(fn,"w").write(body); children[t.strip()]=(fn,len(body))
json.dump({k:v[0] for k,v in children.items()}, open("/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/pages/index.json","w"), indent=1)
print("children:")
for k,(fn,ln) in children.items(): print(f"   {k:34s} {ln:7d} bytes")
raise SystemExit(0)
P.append("<h2>Full per-scenario results</h2>")
P.append(f"<p>All {len(rows)} scenarios, grouped by module.</p>")
cur=None
for t,k,desc,exp,st,note,dfct in rows:
    if t!=cur:
        if cur is not None: P.append("</tbody></table>")
        cur=t
        P.append(f"<h3>{e(t.strip())}</h3><table><tbody><tr><th>Scenario</th><th>Test description</th>"
                 "<th>Expected result</th><th>Actual result</th><th>Status</th><th>Notes / Defect</th></tr>")
    P.append(f"<tr><td>{e(k)}</td><td>{e(desc[:300])}</td><td>{e(exp[:300])}</td><td>{e(note[:700])}</td>"
             f"<td>{loz(st)}</td><td>{e(dfct)}</td></tr>")
P.append("</tbody></table>")
body="".join(P)
open("/home/farsheed/pm-instaprotek/tmp/run-2026-09-16/confluence_body.xml","w").write(body)
print("body bytes:", len(body), "| scenarios:", len(rows))
print("GRAND", g, "| attempted", att)
