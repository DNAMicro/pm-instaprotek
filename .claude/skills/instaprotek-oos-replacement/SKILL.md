---
name: instaprotek-oos-replacement
description: >-
  Draft outbound "claim item out of stock, pick a replacement style" emails from the
  support@instaprotek.com mailbox via Outlook Web in Chrome — never send. Manually triggered: use
  when Sarah says "run OOS emails", "send OOS replacement emails", "out of stock replacement", or
  hands over a photo of claims affected by an out-of-stock item. Looks up each claim in the CRM to
  find the customer's name and email, then creates one unsent draft per claim.
---

# InstaProtek OOS Replacement Emails

Manually-triggered skill: when an item goes out of stock (OOS), draft an email to every affected
customer asking them to pick a replacement style. Every email is an unsent DRAFT in the
support@instaprotek.com mailbox for Sarah to review and send herself — this skill never sends.

## Trigger & input

Sarah runs this by hand each time item(s) go OOS, and provides a **photo** (screenshot of a
claims table). The table is organized in **groups**, each introduced by a highlighted header row
in the form:

`WE HAVE <TYPE> <COLOR>: <Style 1>, <Style 2>, <Style 3>, ... .`

e.g. `WE HAVE WALL WHITE: PREMIUM GLITTER, VELVET (CREAM), WOVEN, DENIM (CREAM), PASTEL BRAIDED,
CORDUROY, NEON.`

Every customer row beneath a header row belongs to that group, until the next header row appears.
**The available replacement styles for a customer's email are whatever comma-separated list sits
in the header row directly above their row** — not a single fixed list for the whole run, and not
necessarily the same list as the group above or below it. Both the number of groups and the
number/names of styles per group vary every run; never reuse a list from a previous run or from
this SKILL.md's own example.

**The claim number is the 4th column** of each customer row (a long numeric ID, distinct from the
12-digit product barcode column and the long tracking-style number further right — go by column
position, not by which number looks most "claim-like").

If no photo is attached when this skill is invoked, ask Sarah for one before doing anything else —
don't guess claim numbers or invent style names.

## Hard rules (non-negotiable)

1. **Never send.** Every email is created and saved as an unsent draft only. If asked to "just
   send it," refuse and point to the Drafts folder in support@instaprotek.com.
2. **Never invent a claim number, name, or email.** Read claim numbers only from column 4 of the
   provided photo, and pull name/email only from the CRM claim record. If a claim can't be found
   in the CRM, or its Customer Details are missing a name or email, skip it, flag it, and report
   it to Sarah rather than guessing.
3. **Never enter CRM or Outlook credentials.** The browser session must already be signed in —
   both the CRM and Outlook Web are expected to already have an active, authenticated session in
   Chrome. If either isn't signed in, stop and tell Sarah to log in first; do not type a password
   anywhere.
4. **Use the exact approved wording** (see "Email content" below) — do not paraphrase the body.
   Only the greeting name, subject claim number, and the style list vary — and the style list for
   each email must come from that customer's group header in this run's photo, never a hardcoded,
   remembered, or previous-run list.
5. **Use the live support signature — do not retype it.** Outlook Web auto-inserts the signature
   when composing from support@instaprotek.com. Type only the greeting + body above it.
6. **One email per claim number**, deduplicated — if the same claim number appears more than once
   in the photo, only draft it once.

## Workflow

1. Read the OOS photo Sarah provided. Walk it top to bottom: each highlighted header row starts a
   new group and defines that group's style list; every row until the next header belongs to that
   group. For each customer row, record its claim number (column 4) and the style list of the
   group it falls under. Dedupe by claim number.
2. For each claim number:
   a. Go to `https://crm.instaprotek.com/portal/claim` in Chrome (assume already signed in) and
      search for the claim number.
   b. Open the claim record and read its **Customer Details** section for the customer's first
      name and email address.
   c. If the claim isn't found, or Customer Details is missing a name or email, skip it and note
      it as a flagged/unresolved row — do not draft an email for it.
3. Open `https://outlook.office.com/mail/support@instaprotek.com/` in Chrome (already signed in
   as support@) and compose a **new message** (not a reply — this is proactive outreach, not a
   response to an existing thread) for each resolved claim, using the content below. Insert the
   greeting + body above the auto-inserted signature; never overwrite it.
4. Save each as a draft (never send).
5. Verify in the Drafts folder that every intended email saved, addressed to the right customer,
   unsent.
6. Save one review file per email in `oos-replacement-emails/drafts/` named
   `YYYY-MM-DD_claim-<claim number>.md`, using `templates/draft_template.md`.
7. Append one row per email to `oos-replacement-emails/drafts/_oos_log.csv`
   (`date,claim_number,customer_email,first_name,subject,file`). Create the file with headers if
   missing.
8. **Commit and push** (`git add -A && git commit -m "OOS replacement emails <date>" && git push`
   via bash), per the project CLAUDE.md.
9. **Post a notification to RingCentral** using the inbound webhook in
   `.claude/skills/instaprotek-enterprise-registration/config/settings.json` (`webhook.url`).
   Include: date, how many claims were in the photo, how many drafts were created, how many were
   skipped/flagged and why, and the commit SHA. State plainly that nothing was sent.
10. Tell Sarah in chat: how many drafts were created, which claims were skipped and why, and that
    they're in `support@instaprotek.com > Drafts` for her to review and send.

## Email content (exact wording — do not paraphrase)

**Subject:** `Claim <claim number>`

**Body** (greeting name, claim number, and the style list are the only substitutions — the body
paragraphs themselves are fixed wording):

```
Hi <First name>,

Thank you for your patience regarding your recent claim. Unfortunately, the item you originally
ordered is currently out of stock. We'd love to send you a replacement and want to make sure you
get something you'll love!

Please take a look at the available styles below and let us know which one you'd prefer:

* <Style 1>
* <Style 2>
* <Style 3 ...>

Simply reply to this email with your preferred style and we'll get it shipped out to you.

Thank you for your understanding, and we appreciate your continued support!
```

Insert that customer's group's exact styles, one per bullet, in the order listed in the header
row. Render each style in Title Case for readability (the source header is in ALL CAPS), keep any
parenthetical qualifier (e.g. "VELVET (CREAM)" → "Velvet (Cream)"), and do not add, drop, rename,
merge, or reorder styles. Two customers in different groups within the same run will get different
bullet lists — that's expected, not an error.

The mailbox signature auto-inserts below this in Outlook Web — do not retype it.

## Reading the OOS photo

The photo is a grouped table: highlighted header rows (`WE HAVE <TYPE> <COLOR>: <styles>.`) each
own the customer rows beneath them until the next header. For every customer row, claim numbers
sit in the **4th column** — a long numeric ID; don't confuse it with the 12-digit product barcode
column or the longer tracking-style number elsewhere in the row. Group labels, style lists, and
which claims are OOS all vary every run — read the actual header text and column 4 values rather
than assuming a fixed position, count, or wording. If a row's 4th-column value doesn't look like a
claim number, or a customer row has no header above it to attach a style list to, flag it rather
than guessing.

## Privacy

Customer emails and names are PII. Keep review files and logs inside `oos-replacement-emails/` in
this project folder; don't paste customer data into web searches.
