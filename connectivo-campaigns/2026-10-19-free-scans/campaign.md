# Connectivo — "Free Accessibility Scan" campaign · week of Oct 19, 2026

**Owner:** Sarah Gamba · **Approver:** Farsheed Atef · **Calls:** Daniel Cyrus Larrobis
**Channels:** Instantly AI (email) + cold calls logged in Zoho CRM
**Builds on:** CC-2 (outreach sequence brief), CC-7 (Canadian cold-calling flow)

## 1. Goal and offer

**Goal:** book free scans with public-sector site owners, then turn the scan report into a remediation call.

**The offer:** we scan their public website at no cost and email them the Connectivo Overview report (PDF). It covers:
- WCAG 2.1 AA violations: affected pages, plus counts by rule (alt text, labels, contrast, …)
- **PDFs and Office files** linked from the site, scanned against PDF/UA-1. Most vendors skip these, so it's our strongest hook.
- Broken links and pages, redirects and blocked pages, which are useful site-health findings on their own

**What the free scan does not include:** fixes. Auto-fix stays **off** on every free scan because fixes cost real AI spend. Remediation is what the follow-up call sells.

**Targets for the week**

| Metric | Target |
|---|---|
| Leads contacted (email) | 150–200 |
| Leads called | 30 |
| Scan requests | 8 |
| Scans delivered | 8 (within 2 business days of request) |
| Remediation calls booked | 3 |

## 2. Audience

- US state and local government: cities, counties, school districts, special districts, transit and utilities. These are the ADA Title II entities.
- Pull from the existing Zoho lead lists (CC-4 / CC-6) plus TLG conference contacts not yet emailed.
- Contact: web manager, IT director, communications director, ADA coordinator or city clerk.
- Exclude anyone already in an active Instantly sequence, plus customers and current prospects.

## 3. Schedule — Mon Oct 19 to Fri Oct 23

| Day | What | Who |
|---|---|---|
| **Mon 10/19** | Approve copy · build the lead list in Zoho, export to Instantly · run a spam check on all copy · confirm the scan cap and prospect org (§7) | Sarah, Farsheed |
| **Tue 10/20** | Email 1 goes out 9–11am in the recipient's time zone | Instantly |
| **Wed 10/21** | Call block 1: openers who didn't reply (~15 calls) · fulfil any scan requests | Daniel, Sarah |
| **Thu 10/22** | Email 2 to non-repliers | Instantly |
| **Fri 10/23** | Call block 2 (~15 calls) · deliver the remaining scans · weekly tally (§8) | Daniel, Sarah |
| *Tue 10/27* | *Email 3 (breakup) — the sequence's last step, sent automatically* | *Instantly* |

Instantly settings: send Mon–Fri only, stop on reply, ≤ 30 sends per inbox per day, open tracking **off** (it hurts deliverability). Watch replies instead of open rates.

## 4. Email sequence (Instantly)

Variables: `{{firstName}}`, `{{companyName}}`, `{{city}}`, `{{state}}`, `{{website}}`.
Subject lines avoid "FREE" in caps and exclamation marks, for spam scoring. A/B test the first two options of each email.

### Email 1 — Tue 10/20

**Subject options:** `{{companyName}} website accessibility` · `a quick scan of {{website}}` · `PDFs on {{website}}`

> Hi {{firstName}},
>
> Accessibility reviews of public websites usually check the pages and stop. Most of the risk for a public agency sits in the PDFs: agendas, budgets, forms.
>
> We'll run a free accessibility scan of {{website}}, covering pages **and** linked documents against WCAG 2.1 AA, and email you the report. It's free, with no call required to get it.
>
> Want me to set it up for {{companyName}}?
>
> Sarah Gamba
> Connectivo by DNA Micro

*(~75 words)*

### Email 2 — Thu 10/22

**Subject options:** `re: {{companyName}} website accessibility` · `what the scan shows`

> Hi {{firstName}},
>
> Quick follow-up. The report shows how many of your pages and documents have WCAG violations, which rules they break, and any broken links and redirects we find along the way.
>
> Where we differ from most vendors is what comes next: Connectivo fixes the issues itself and re-scans to prove each fix worked. It does that without access to your source code or changes to your web server.
>
> Should I run the scan on {{website}}? A one-word reply is fine.
>
> Sarah

*(~80 words)*

### Email 3 (breakup) — Tue 10/27

**Subject options:** `close the loop?` · `{{website}} scan`

> Hi {{firstName}},
>
> I won't keep filling your inbox. If website accessibility for {{companyName}} belongs to someone else, could you point me to them?
>
> The free scan offer stands. Reply "scan" any time and I'll send the report within two business days.
>
> Sarah

*(~50 words)*

### Footer (every email: CAN-SPAM)

> Connectivo · DNA Micro · `[PHYSICAL MAILING ADDRESS — fill in before launch]`
> Not the right person, or prefer not to hear from us? Reply "unsubscribe" and we'll remove you.

Also enable Instantly's unsubscribe link.

## 5. Call script (Wed and Fri blocks)

**Who to call:** contacts who didn't reply. Prioritise anyone who opened or clicked, if Instantly shows it.

> "Hi {{firstName}}, this is Daniel with Connectivo at DNA Micro. Sarah emailed you this week about a free accessibility scan of your website. Did you get a chance to see it?
>
> *[If no / not sure]* In short, we scan your public site for WCAG problems, including the PDFs like agendas and budgets that most reviews skip, and email you the report. It costs nothing and you don't need to meet with us to get it.
>
> Who's the best person to send it to?"

- **Yes:** confirm the website URL and the email address for the report. Create a Zoho task "Free scan — {{companyName}}" and assign it to Sarah.
- **Wrong person:** get the name and email of the right person. Add them to Zoho as a new lead, with a note.
- **Not interested:** ask "Is accessibility already handled by a vendor?" Log the answer.
- **Voicemail:** leave a 20-second voicemail that names the free scan and says "check your email from Sarah."

Log every real interaction as a Zoho note, as in CC-7. No-answer and unreachable calls don't need a note.

## 6. Fulfilling a scan request

1. In Zoho, set the lead status to **Scan requested**.
2. In the Connectivo portal (production), create the site under the **prospects org** (see §7). Use these settings:
   - **Audit coverage:** Full site, capped (see §7)
   - **Page and file accessibility audit:** ON
   - **Page and file automated fixes:** **OFF**
   - **Auto-publish:** OFF
   - **AI knowledge base:** OFF
   - **Schedule:** Audit now
3. When the audit completes, review the Overview yourself before sending. If there are many failed or blocked pages (bot detection, 403s), say so in the email instead of sending a misleading report.
4. Send the report with **Share report** to the prospect, or export the PDF and reply in the thread, using the template below.
5. In Zoho, set the lead status to **Scan delivered** and create a follow-up task for 2 business days later.

**Report delivery email**

> Hi {{firstName}},
>
> Your accessibility report for {{website}} is attached. The headline figures: **[X] pages and [Y] documents with violations**, with the most common issues being **[top 2 rules]**.
>
> Every one of these can be fixed automatically, without touching your web server. Do you have 20 minutes this week or next to walk through it?
>
> Sarah

## 7. Decisions before Tuesday's send

| # | Decision | Suggested default |
|---|---|---|
| 1 | Page cap per free scan, to keep crawl time and cost bounded | Full site, maximum 500 pages and 200 files; use exclusions for anything larger |
| 2 | Which portal org holds prospect sites | A dedicated "Connectivo Prospects" org, not *Connectivo Testing* |
| 3 | Physical mailing address for the CAN-SPAM footer | DNA Micro office address |
| 4 | Sending domains / inboxes warmed (CC-1 is still To Do) | Don't launch on cold inboxes. If they aren't warmed, run calls only this week and start the emails next week |
| 5 | Mention ADA Title II compliance dates in the copy? | Leave them out for now. Add them only after confirming the current DOJ deadlines |

## 8. Friday tally (paste into CC ticket / RingCentral)

```
Connectivo free-scan campaign — week of 10/19
Emails sent: __ | Replies: __ (positive __ / negative __ / unsubscribes __)
Calls: __ made | __ conversations | __ voicemails
Scan requests: __ | Scans delivered: __
Remediation calls booked: __
Notes / objections heard:
```
