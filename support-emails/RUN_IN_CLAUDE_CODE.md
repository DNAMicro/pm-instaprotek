# Run support-email drafting from Claude Code (read -> draft -> Outlook Drafts)

## Before you run
- Start Claude Code from the `pm-instaprotek` folder (loads the project skill + CLAUDE.md).
- Have classic desktop Outlook open and signed in (the push step drives it).
- First time only: if Claude Code says the Microsoft 365 connector needs auth, run `/mcp` and connect it.

## Paste this into Claude Code

Run the instaprotek-support-emails skill. Read the new customer inquiries in the
support@instaprotek.com mailbox via the Microsoft 365 connector. For each inquiry, follow the
skill exactly: use canned response #1 for device / product-list confusion ("cannot find
company/brand/product", "add device/model/brand", entering make & model), canned response #3 for
connection / server errors, and the DEFAULT "how can we help you" response for anything else -
do not compose a bespoke reply for uncovered cases. Ground any factual answer in
support-emails/reference/. Never offer refunds, replacements, discounts, credits, free items, or
any other concession - if the customer asks for one, flag the draft NEEDS APPROVAL. Never invent
facts (order numbers, coverage, timelines) - use [NEEDS INFO] instead. Flag legal threats,
chargebacks, injury/safety, or press as ESCALATE. Skip automated / internal mail (tawk.to,
anything @liquipel.com). Save one draft .md per inquiry in support-emails/drafts/ and append a row
to _draft_log.csv, then run support-emails/push_drafts_to_outlook.ps1 so the drafts appear in my
Outlook Drafts with From = support@instaprotek.com. Do NOT send anything. Finish by telling me how
many drafts you created and which are flagged NEEDS APPROVAL / NEEDS INFO / ESCALATE.

## After it runs
Open Outlook > Drafts, review each (especially the flagged ones), and send from support@instaprotek.com.
