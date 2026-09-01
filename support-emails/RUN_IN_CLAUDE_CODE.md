# Run support-email drafting from Claude Code (read -> reply in-thread -> support mailbox Drafts)

## Before you run
- Start Claude Code from the `pm-instaprotek` folder (loads the project skill + CLAUDE.md).
- Have Chrome open and signed in to the support mailbox (`support@instaprotek.com`) in Outlook Web.
  Desktop Outlook is no longer used — drafts are created in the support mailbox itself.

## Paste this into Claude Code

Run instaprotek support email. Respond to each unread Focused email as a reply, use the support
signature, do not send — just leave them in drafts. Make each reply a conversation (in-thread).
Access the support mailbox through Claude Chrome and respond from there, not in my dnamicro email.
Once done, send a success notification in the RingCentral channel.

## What it does
1. Opens `https://outlook.office.com/mail/support@instaprotek.com/` in Chrome and lists the unread
   Focused conversations (reports the real count).
2. Reads each thread in full, including prior support replies.
3. Creates an **in-thread reply draft** in `support@instaprotek.com > Drafts` — unsent, with the
   mailbox signature auto-applied (never retyped).
4. Uses `reference/canned_responses.md` (#1 product-list, #2 default, #3 connection, #4 one claim
   per registration); short bespoke replies only where the default would clearly be wrong.
5. Never offers refunds, replacements, or other concessions — those get flagged `NEEDS APPROVAL`.
   Missing facts get `[NEEDS INFO]`; legal/chargeback/injury/press or a stuck repeat contact gets
   `ESCALATE`.
6. Saves a review `.md` per draft in `drafts/` plus a row in `_draft_log.csv`, commits and pushes.
7. Posts a success notification to the RingCentral channel with the counts and flag breakdown.

## After it runs
Open the **support mailbox** (`support@instaprotek.com`) > Drafts, review each reply — especially
the flagged ones — and send from there. Never send from `sarah@dnamicro.com` or `admin@`.
