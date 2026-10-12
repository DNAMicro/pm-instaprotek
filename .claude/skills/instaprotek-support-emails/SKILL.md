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
   draft files only. If asked to "just send it", refuse and point to the drafts folder.
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
5. **Always notify RingCentral.** Every run ends with a post to the RingCentral webhook —
   success or failure, whether or not anyone asked for it. Never skip it and never wait to be
   prompted. See "RingCentral notification" below.

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

1. **Microsoft 365 connector (preferred):** use `outlook_email_search` to pull the relevant
   message(s) — e.g. unread in the support mailbox, or the message Sarah describes. Read-only.
2. **Files:** any .eml/.msg/.txt/.pdf/.md dropped in `support-emails/inbox/`.
3. **Pasted text** in the conversation.

## Reference material

Ground every factual claim in `support-emails/reference/` (FAQ, policies, canned answers,
plan/coverage docs). Check it before drafting. If reference docs don't cover the question,
say so in the review header and use `[NEEDS INFO]` in the body rather than guessing.

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
5. **Commit and push** (`git add -A && git commit -m "Support emails <date>: <n> drafts" &&
   git push` via bash), per the project CLAUDE.md.
6. **Post the RingCentral notification** — always, see below.
7. Tell Sarah in chat: how many drafts, which are flagged `NEEDS APPROVAL` / `ESCALATE` /
   `NEEDS INFO`, and where they are. She reviews, edits, and sends from Outlook herself.

## RingCentral notification

Post to the inbound webhook at `webhook.url` in
`.claude/skills/instaprotek-enterprise-registration/config/settings.json`. It takes a simple JSON
body — `{"title": "...", "text": "..."}` — with markdown in `text`.

Send it on **every** run without being asked, including runs that drafted nothing, were cut short,
or failed partway. On a failure, say so in the title and name the stage it failed at; never stay
silent about a run that happened.

Include:

- the run date, and how many conversations were in the inbox
- how many drafts were created, plus how many were skipped and why
- the category breakdown and the flag counts (`ESCALATE` / `NEEDS APPROVAL` / `NEEDS INFO`)
- each `ESCALATE` case by name with a one-line reason
- the commit SHA
- a plain statement that **nothing was sent**

Keep customer detail to names and one-line reasons — no addresses, order contents, or full
message bodies in the channel. Save the webhook response to
`support-emails/drafts/_webhook_<date>.json` so the post is auditable.

## Escalation flags

Flag `ESCALATE` (and keep the draft to a brief, neutral holding reply): legal threats or
lawyers, chargebacks/payment disputes, injury/safety claims, press/media, regulator mentions,
or a repeat contact that's escalating in anger. Note why in the review header.

## Privacy

Customer emails contain PII. Keep contents inside this project folder; don't paste customer
data into web searches; drafts and logs stay in `support-emails/`.
