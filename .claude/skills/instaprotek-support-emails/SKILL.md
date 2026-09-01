---
name: instaprotek-support-emails
description: >-
  Draft in-thread replies to InstaProtek customer support emails inside the
  support@instaprotek.com mailbox via Outlook Web in Chrome — never send. Use when the user says
  "answer support emails", "run instaprotek support email", "draft support replies", "process the
  support inbox", "respond to this customer email", drops emails into support-emails/inbox/, or
  pastes a customer inquiry. Finishes by posting a success notification to RingCentral.
---

# InstaProtek Support Email Drafting

Draft replies to incoming support emails about the InstaProtek portal, registrations, plans,
claims, repairs, and buyback. Every reply is an unsent DRAFT for Sarah to review, saved as a
reply **inside the customer's existing conversation** in the support mailbox itself.

## Hard rules (non-negotiable)

1. **Never send.** Do not send email through any connector, browser, or script. Every reply stays
   an unsent draft. If asked to "just send it", refuse and point to the Drafts folder.
2. **Reply in-thread, never a new message.** Open the customer's conversation and use its
   **Reply** button so the draft threads under their message (subject becomes `Re: …`). Do not
   compose a fresh email to the customer's address — that breaks the conversation.
3. **Draft in the support mailbox, not Sarah's.** Drafts must land in
   `support@instaprotek.com > Drafts`, created by driving Outlook Web in Chrome. Never draft or
   send from `sarah@dnamicro.com` / `admin@`, and do NOT run
   `support-emails/push_drafts_to_outlook.ps1` — it writes to the desktop Outlook profile's own
   Drafts, which is not where Sarah looks. (The script is kept only as a legacy fallback.)
4. **Use the live support signature — do not retype it.** Outlook Web auto-inserts the signature
   when a reply is opened from support@instaprotek.com. Type only the greeting and body, above the
   signature. Retyping it produces a duplicate.
5. **No concessions without explicit approval.** Never offer refunds, replacements, discounts,
   credits, free services/months, waived fees, coverage exceptions, or policy overrides unless
   Sarah has explicitly approved that specific concession in this conversation. If the customer
   requests one, draft an empathetic reply that acknowledges the request without promising it,
   and flag the draft `NEEDS APPROVAL`.
6. **Never invent facts.** No made-up order numbers, coverage terms, timelines, or policy
   details. If the answer isn't in the reference docs or the email itself, insert
   `[NEEDS INFO: …]` in the review header and flag the draft.
7. **No commitments on timelines** ("within 24 hours", "by Friday") unless documented in
   reference docs.

## Tone

Customer-centric and human — warm, direct, competent. Must NOT read as AI-generated:

- No "I hope this email finds you well", "Thank you for reaching out" openers on every draft,
  "I sincerely apologize for any inconvenience this may have caused", or stacked apologies.
- No bullet-point walls in customer replies; write short natural paragraphs.
- Use the customer's first name, mirror their formality, vary sentence rhythm.
- One clear apology max when something went wrong, then focus on what happens next.
- Plain words over corporate ones (use "fix", not "rectify"; "send", not "provide").
- Sign-off is the mailbox signature (`Best Regards,` / `Instaprotek Support Team` /
  `support@instaprotek.com` / office hours / `www.instaprotek.com`). Use a name only if Sarah
  specifies one.

## Sources of incoming email

1. **Outlook Web in Chrome (primary):** `https://outlook.office.com/mail/support@instaprotek.com/`
   — the browser is already signed in as support@. This is both how you read the mail and where
   the drafts are created. See *Driving Outlook Web* below.
2. **Microsoft 365 connector (read-only fallback):** `outlook_email_search` with
   `mailboxOwnerEmail: support@instaprotek.com`. Useful for lookups, but it cannot create the
   in-thread drafts in the support mailbox — do not use it as the delivery path.
3. **Files:** any .eml/.msg/.txt/.pdf/.md dropped in `support-emails/inbox/`.
4. **Pasted text** in the conversation.

## Driving Outlook Web (verified 2026-09-01)

- Resize the viewport tall (~1500×1800) so the virtualized message list renders ~20 rows at once.
- Unread Focused rows are `div[role="option"]` whose `aria-label` starts with `Unread`. Read the
  row count from `aria-setsize`, and scroll the nearest `overflow-y: auto` ancestor to load the
  rest. Report the real count if it differs from what Sarah said.
- Read a thread by clicking its row and taking `document.querySelector('[role="main"]').innerText`
  — that gives the full conversation including prior support replies (check them: they change the
  right answer, and a third unresolved contact is an `ESCALATE`).
- To draft: click the first `Reply` button, then insert the greeting + body **above** the
  auto-inserted signature — collapse a `Range` to offset 0 of
  `[contenteditable="true"][aria-label="Message body"]` and
  `document.execCommand('insertHTML', …)`. Never overwrite the editor's contents (that wipes the
  signature).
- **Switching to another thread auto-saves the draft**, so a whole batch of replies runs in one
  `browser_evaluate` call — no `Ctrl+S` per message.
- Navigating away with a compose still open raises a `beforeunload` dialog: dismiss it, press
  `Ctrl+S`, then navigate.
- Verify at the end by opening the **Drafts** folder and counting the `[Draft]` rows — each should
  read `[Draft] <customer> Re: <subject>`.

## Reference material

Ground every factual claim in `support-emails/reference/` (FAQ, policies, canned answers,
plan/coverage docs). Check it before drafting. If reference docs don't cover the question,
say so in the review header and use `[NEEDS INFO]` rather than guessing.

## Canned responses (apply first)

Before drafting from scratch, check `support-emails/reference/canned_responses.md` — it holds the
approved wording. Match the inquiry to a rule and use that response, personalizing the greeting
with the first name if known:

- **#1 Device make/model or product-list confusion** — asks about entering device make & model, the
  "product list", or says "cannot find company / brand / product" or "add device / model / brand":
  the list is for their device (where the app is installed), not the product; the product is
  already recognized from the scanned barcode; enter the phone's make and model to proceed.
- **#2 Default (catch-all)** — anything not clearly matching another rule, including empty or
  photo-only emails and anything you're unsure about: use the "share a few details" response and
  let Sarah handle the specifics.
- **#3 Connection / server error** — "cannot connect to server", "unable to connect", the app not
  connecting or locking up: ask if it's still happening, advise uninstall/reinstall to refresh the
  server connection, then register again.
- **#4 "File a Claim" not working / claim already used** — the button is greyed out or the app says
  a claim was already filed: one registration is to one claim only; register again with the barcode
  shown in the account, upload any photo when asked for the receipt, then claim against the new
  registration.

**When the default would clearly be wrong**, a short bespoke reply is allowed — the customer already
gave full detail, already answered our question, or is just saying thanks. Keep it to two or three
lines, make no factual claim that isn't already in the thread, and flag it `NEEDS APPROVAL` (or
`NEEDS INFO` where an action is owed) with a note in the review header. When genuinely in doubt,
use #2.

Still never send; still flag `NEEDS APPROVAL` if the customer also asks for a refund, replacement,
or other concession.

Skip automated and internal mail (tawk.to, anything @liquipel.com) and cold sales solicitations —
don't draft a reply, just report them as skipped.

## Workflow

1. Open the support mailbox in Chrome and list the unread Focused conversations; report the count.
2. Read every thread in full (batch the reads — one `browser_evaluate` can walk several rows).
3. For each: classify (registration / claim / coverage question / repair / buyback / billing /
   account / complaint / other), check reference docs, pick the canned response, and create the
   **in-thread reply draft** in the support mailbox. Batch these too.
4. Verify in the Drafts folder that every reply saved, threaded and unsent.
5. Save one review file per draft in `support-emails/drafts/` named
   `YYYY-MM-DD_<from-or-subject-slug>.md` using `templates/draft_template.md`: review header
   (category, the ask, flags, refs used, notes) then the reply as sent. These are review notes —
   the mailbox draft is the deliverable.
6. Append a row per draft to `support-emails/drafts/_draft_log.csv`
   (`date,from,subject,category,flags,file`). Create the file with headers if missing.
7. **Commit and push** (`git add -A && git commit -m "…" && git push` via bash), per the project
   CLAUDE.md.
8. **Post a success notification to RingCentral** using the inbound webhook in
   `.claude/skills/instaprotek-enterprise-registration/config/settings.json` (`webhook.url`).
   Include: date, mailbox, conversations reviewed, replies drafted, anything skipped, the flag
   breakdown (`ESCALATE` / `NEEDS APPROVAL` / `NEEDS INFO` with names), canned-response mix, and
   the commit SHA. State plainly that nothing was sent. Post the notification on failure too — say
   what stage broke and how many drafts made it.
9. Tell Sarah in chat: how many drafts, which are flagged and why, and that they're in
   `support@instaprotek.com > Drafts` for her to review and send from the support mailbox.

## Escalation flags

Flag `ESCALATE` (and keep the draft to a brief, neutral holding reply): legal threats or
lawyers, chargebacks/payment disputes, injury/safety claims, press/media, regulator mentions,
or a repeat contact that's still unresolved after two or more support replies. Note why in the
review header.

## Privacy

Customer emails contain PII. Keep contents inside this project folder; don't paste customer
data into web searches; drafts and logs stay in `support-emails/`.
