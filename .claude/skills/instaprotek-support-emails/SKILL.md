---
name: instaprotek-support-emails
description: >-
  Draft replies to InstaProtek customer support emails for human review — never send.
  Use when the user says "answer support emails", "draft support replies", "process the
  support inbox", "respond to this customer email", drops emails into support-emails/inbox/,
  or pastes a customer inquiry. Reads Outlook via the Microsoft 365 connector when available.
---

# InstaProtek Support Email Drafting

Draft replies to incoming support emails about the InstaProtek portal, registrations, plans,
claims, repairs, and buyback. Every reply is a DRAFT for Sarah to review. Nothing is ever sent.

## Hard rules (non-negotiable)

1. **Never send.** Do not send email through any connector, browser, or script. Output is
   draft files (and, when run on the desktop, unsent Outlook drafts created by `push_drafts_to_outlook.ps1`, which only saves drafts and never sends) only. If asked to "just send it", refuse and point to the drafts folder.
2. **No concessions without explicit approval.** Never offer refunds, replacements, discounts,
   credits, free services/months, waived fees, coverage exceptions, or policy overrides unless
   Sarah has explicitly approved that specific concession in this conversation. If the customer
   requests one, draft an empathetic reply that acknowledges the request without promising it,
   and flag the draft `NEEDS APPROVAL`.
3. **Never invent facts.** No made-up order numbers, coverage terms, timelines, or policy
   details. If the answer isn't in the reference docs or the email itself, insert
   `[NEEDS INFO: …]` and flag the draft.
4. **No commitments on timelines** ("within 24 hours", "by Friday") unless documented in
   reference docs.

## Tone

Customer-centric and human — warm, direct, competent. Must NOT read as AI-generated:

- No "I hope this email finds you well", "Thank you for reaching out" openers on every draft,
  "I sincerely apologize for any inconvenience this may have caused", or stacked apologies.
- No bullet-point walls in customer replies; write short natural paragraphs.
- Use the customer's first name, mirror their formality, vary sentence rhythm.
- One clear apology max when something went wrong, then focus on what happens next.
- Plain words over corporate ones (use "fix", not "rectify"; "send", not "provide").
- Sign off: `InstaProtek Support` unless Sarah specifies a name.

## Sources of incoming email

1. **Microsoft 365 connector (preferred):** use `outlook_email_search` with
   `mailboxOwnerEmail: support@instaprotek.com` (the support mailbox — shared/delegated) to pull
   the relevant message(s) — e.g. recent unread, or the message Sarah describes. Read-only.
2. **Files:** any .eml/.msg/.txt/.pdf/.md dropped in `support-emails/inbox/`.
3. **Pasted text** in the conversation.

## Reference material

Ground every factual claim in `support-emails/reference/` (FAQ, policies, canned answers,
plan/coverage docs). Check it before drafting. If reference docs don't cover the question,
say so in the review header and use `[NEEDS INFO]` in the body rather than guessing.

## Canned responses (apply first)

Before drafting from scratch, check `support-emails/reference/canned_responses.md`. If the inquiry
matches one of these, use that approved response (personalize the greeting with the first name if known):

- **Device make/model or product-list confusion** - asks about entering device make & model, the
  "product list", or says "cannot find company / brand / product" or "add device / model / brand":
  explain the list is for their device (where the app is installed), not the product; the product is
  already recognized from the scanned barcode; enter the phone's make and model to proceed.
- **Empty email or photo only (no details)** - reply asking how you can help and for a few details.
- **Connection / server error** - "cannot connect to server", "unable to connect", or anything about
  connectivity: ask if it's still happening, advise uninstall/reinstall to refresh the server
  connection, then register again.

Use the wording in `canned_responses.md` for these. Still never send; still flag NEEDS APPROVAL if
the customer also asks for a refund/replacement/other concession.

## Workflow

1. Collect the email(s) from connector, inbox folder, or paste.
2. For each email: classify (registration / claim / coverage question / repair / buyback /
   billing / account / complaint / other), check reference docs, then draft.
3. Save one file per draft in `support-emails/drafts/` named
   `YYYY-MM-DD_<from-or-subject-slug>.md` using `templates/draft_template.md`:
   a review header (category, summary of the ask, flags, refs used), then the ready-to-paste
   reply (To / Subject / body).
4. Append a line to `support-emails/drafts/_draft_log.csv`
   (`date,from,subject,category,flags,file`). Create the file with headers if missing.
5. **Load the drafts into Outlook (when running on the desktop).** Run `support-emails/push_drafts_to_outlook.ps1` in PowerShell to create each draft in the Outlook Drafts folder, From `support@instaprotek.com` - it saves drafts only and never sends (needs classic desktop Outlook). If there's no desktop Outlook available (e.g. running in Cowork), skip this and leave the draft files for a manual push.
6. Tell Sarah in chat: how many drafts, which are flagged `NEEDS APPROVAL` / `ESCALATE` /
   `NEEDS INFO`, and where they are. She reviews, edits, and sends from Outlook herself —
   **always from the support mailbox (support@instaprotek.com), never from admin@ or a
   personal account.** Every draft carries a `From: support@instaprotek.com` line as a reminder.

## Escalation flags

Flag `ESCALATE` (and keep the draft to a brief, neutral holding reply): legal threats or
lawyers, chargebacks/payment disputes, injury/safety claims, press/media, regulator mentions,
or a repeat contact that's escalating in anger. Note why in the review header.

## Privacy

Customer emails contain PII. Keep contents inside this project folder; don't paste customer
data into web searches; drafts and logs stay in `support-emails/`.
