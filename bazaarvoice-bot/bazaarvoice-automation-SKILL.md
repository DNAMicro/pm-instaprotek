---
name: bazaarvoice-automation
description: Set up and deploy automated customer review responses for Bazaarvoice. Use this skill when you need to create a Node.js/Playwright bot that responds to unread product reviews on Bazaarvoice with warm, on-brand replies. Covers the complete workflow: understanding the automation architecture, securing credentials, writing response logic for different review types (positive feedback, product defects, charging issues), local testing, and cloud server deployment. Includes best practices for handling sensitive credentials and examples of review response patterns. Invoke this skill whenever you need to automate Bazaarvoice review management, set up review response workflows, or deploy customer response automation to a server.
---

# Bazaarvoice Review Response Automation

## Overview

This skill guides you through building and deploying an automated system to respond to customer reviews on Bazaarvoice using Node.js and Playwright. The bot handles filtering, drafting warm responses following brand guidelines, and posting responses directly to the platform.

## When to Use This Skill

- **Setting up automated review responses** for e-commerce products
- **Deploying a review bot** to a cloud server
- **Managing review response workflows** with custom brand guidelines
- **Handling different review types** (complaints, positive feedback, technical issues) programmatically
- **Securing credentials** for platform integrations

## Architecture Overview

```
Your Local Development
    ↓
├── Files: package.json, bazaarvoice-bot.js, config.json
├── Credentials: credentials.json (local only, .gitignore)
└── Push to GitHub (credentials excluded)
    ↓
Cloud Server Deployment
    ├── Clone repo
    ├── Install dependencies
    ├── Set environment credentials
    └── Run bot on schedule or manually
```

## Step 1: Understand the Workflow

The Bazaarvoice bot performs these steps:

1. **Login** — Authenticate to the Bazaarvoice portal using stored credentials
2. **Navigate** — Reach the review inbox (see "Reaching the review inbox" below)
3. **Filter** — Show reviews that have not been responded to
4. **Process** — For each review:
   - Read and understand the customer's feedback
   - Determine review type (positive, defect, charging issue, etc.)
   - Draft an appropriate response
   - Validate the draft against the brand rules
   - Post the response (only when run with `--post`)
5. **Notify** — Post a success notification to RingCentral at the end of every run

## Reaching the review inbox (IMPORTANT)

Do **not** navigate straight to `https://response.bazaarvoice.com/#/respond`. That URL
redirects back to `portal.bazaarvoice.com/home` and the run finds zero reviews. The only
reliable route is the one a person takes:

1. Log in, landing on `https://portal.bazaarvoice.com/home`
2. Click **More** in the top nav
3. Click **Connections** — this is a `button[role="menuitem"]`, not a link, and it
   **opens a new browser tab** at `https://response.bazaarvoice.com/#/connections`.
   The automation must capture that popup tab and keep working in it.
4. In the new tab, click **Questions and Reviews** in the top nav. This lands on
   `https://response.bazaarvoice.com/#/respond`, the review inbox.

### Filters

In the "Refine Your Results" sidebar, select:

| Filter group | Value | Why |
|---|---|---|
| Content | **Reviews** | Skips shopper questions, which need a different answer style |
| State | **Without any response** | This is what "not yet responded" actually means. "Unread" is a different axis and will miss reviews |
| Time | **Any Time** | Combined with the age rule below |

**Age rule: disregard reviews that are a year old or older.** Cards show relative
timestamps ("3 months ago", "a year ago"); anything at or past twelve months is skipped
in code via `filters.max_age_months`. Filtering by "Last month" in the UI instead is too
narrow and typically returns zero rows.

### Useful selectors

| Thing | Selector |
|---|---|
| Review card | `[ng-repeat="content in contentStore.contents"]` |
| Star rating | `.response-star-on`, read `style.width` (100% = 5 stars, 60% = 3) |
| Result counter | text matching `of [0-9,]+` |
| Cookie banner | `#onetrust-accept-btn-handler` (it blocks clicks until dismissed) |

The sidebar filters are plain Angular text nodes, so click them with an exact text
match such as `:text-is("Without any response")`.

## Step 2: Project Setup

### Local Development Files

Create these files in your project root:

**`package.json`** — Node.js dependencies
```json
{
  "name": "bazaarvoice-review-bot",
  "version": "1.0.0",
  "description": "Automate customer review responses on Bazaarvoice",
  "main": "bazaarvoice-bot.js",
  "scripts": {
    "start": "node bazaarvoice-bot.js"
  },
  "dependencies": {
    "playwright": "^1.40.0"
  }
}
```

**`config.json`** — Non-sensitive settings (safe for GitHub)
```json
{
  "bazaarvoice_url": "https://response.bazaarvoice.com/#/respond",
  "filters": {
    "content_type": "Reviews",
    "state": "Without any response",
    "time_range": "Any Time",
    "max_age_months": 12
  },
  "browser": {
    "headless": false,
    "timeout": 30000
  },
  "response_rules": {
    "no_dashes": true,
    "vary_openings": true,
    "closing": "Thank you!",
    "support_email": "ecom@liquipel.com",
    "support_phone": "1 855 478 4735",
    "support_hours": "Monday to Friday, 8 AM to 5 PM Pacific Time"
  },
  "webhook": {
    "url": "https://hooks.ringcentral.com/webhook/v2/...",
    "timeout_seconds": 15,
    "notify_on": "every run, success and failure"
  }
}
```

**`credentials.json.example`** — Template only (commit to GitHub)
```json
{
  "bazaarvoice": {
    "username": "your_email@example.com",
    "password": "your_password",
    "url": "https://response.bazaarvoice.com/#/respond"
  }
}
```

**`.gitignore`** — Keep secrets out of GitHub
```
node_modules/
credentials.json
.env
.env.local
*.log
.DS_Store
```

### Installation

```bash
# Create folder and initialize
mkdir bazaarvoice-bot && cd bazaarvoice-bot

# Copy the files above into this folder

# Install dependencies
npm install

# Create credentials file (copy from template)
cp credentials.json.example credentials.json
# Edit credentials.json with your actual Bazaarvoice login
```

## Step 3: Core Bot Script

Create **`bazaarvoice-bot.js`** to handle the automation:

```javascript
const { chromium } = require('playwright');
const config = require('./config.json');
const credentials = require('./credentials.json');

async function loginToBazaarvoice(page) {
  console.log('🔓 Logging in to Bazaarvoice...');
  await page.goto(credentials.bazaarvoice.url, { waitUntil: 'networkidle' });
  
  // Fill login form (adjust selectors based on actual page)
  await page.fill('input[type="email"]', credentials.bazaarvoice.username);
  await page.fill('input[type="password"]', credentials.bazaarvoice.password);
  await page.click('button[type="submit"]');
  
  await page.waitForNavigation({ waitUntil: 'networkidle' });
  console.log('✅ Logged in');
}

async function filterReviews(page) {
  console.log('🔍 Applying filters...');
  // Click Unread filter
  await page.click('text=Unread');
  // Click Last Month filter
  await page.click('text=Last month');
  await page.waitForTimeout(2000);
  console.log('✅ Filters applied');
}

async function draftResponse(reviewText, reviewerName) {
  // Detect review type and draft appropriate response
  
  if (reviewText.toLowerCase().includes('love') || reviewText.toLowerCase().includes('excellent')) {
    return `We're thrilled you're happy with your product! Thank you!`;
  }
  
  if (reviewText.toLowerCase().includes('not work') || reviewText.toLowerCase().includes('broken')) {
    return `We're sorry this didn't work as expected. We'd like to make it right. Please reach out to our support team at ${config.response_rules.support_email} or call ${config.response_rules.support_phone} (${config.response_rules.support_hours}) for a replacement. Thank you!`;
  }
  
  if (reviewText.toLowerCase().includes('charging')) {
    return `Thanks for your feedback. Fast charging requires pairing with a compatible fast charging adapter and device. For assistance, contact ${config.response_rules.support_email} or ${config.response_rules.support_phone} (${config.response_rules.support_hours}). Thank you!`;
  }
  
  return `Thank you for taking the time to share your feedback!`;
}

async function main() {
  const browser = await chromium.launch({ headless: config.browser.headless });
  const page = await browser.newPage();
  
  try {
    await loginToBazaarvoice(page);
    await filterReviews(page);
    
    // Get reviews and respond to each
    console.log('📋 Processing reviews...');
    // (Add logic to extract and respond to each review)
    
    console.log('✅ Done!');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
```

## Step 4: Response Style Guidelines

All responses must follow these rules:

**Tone**
- Warm and customer-centric
- Address by name when available (e.g., "Hi Sarah,") — never invent names
- Vary opening phrases across responses

**Format**
- No dashes of any kind (em-dash, en-dash, hyphens as connectors)
- Close with "Thank you!" — never "have a great day"

**Handling Review Types**

| Review Type | Response Approach |
|---|---|
| **Positive** | 1-2 sentences, no support info needed |
| **Defect/Damage** | Apologize, offer replacement via support contact, weave naturally into text |
| **Charging Issue** | Note that fast charging needs compatible adapter + device, offer support |
| **Mixed** | Address positive, then handle the issue |

**Support Contact Format**
- Embed naturally: "We'd like to help—please reach out to ecom@liquipel.com or call 1 855 478 4735 (Monday to Friday, 8 AM to 5 PM Pacific Time)"
- Never mention refunds
- Don't troubleshoot; offer replacement only

## Step 5: Local Testing

```bash
# Install dependencies (first time only)
npm install
npx playwright install chromium

# Offline check of the drafting and brand rules, no login needed
node bazaarvoice-bot.js --self-test

# Dry run against the live inbox: logs in, filters, drafts, posts NOTHING
node bazaarvoice-bot.js --limit 8

# Post for real
node bazaarvoice-bot.js --post
```

The bot is **dry run by default** and only posts when `--post` is passed. Every run
writes screenshots and a `report.json` under `runs/<timestamp>/`.

**Debugging tips:**
- If selectors fail, inspect the Bazaarvoice page and update selectors in the script
- Use `page.screenshot()` to debug page state
- Check browser console for JavaScript errors

## Posting responses

The response editor is inline in each review card:

| Element | Selector |
|---|---|
| Form | `form[name="responseForm"]` (`ng-submit="publish()"`) |
| Reply box | `textarea[ng-model="text"]` |
| Submit | `input[type="submit"][value="Respond"]` (`.respond-button`) |
| Cancel | `input[type="reset"][value="Cancel"]` |

The Respond button stays hidden until the reply box is clicked, so click the box first,
then fill it. Playwright's `fill()` drives the Angular binding correctly: the form flips
to `ng-valid` once text lands.

**Find the card by its review text, never by index.** Publishing removes a review from the
"Without any response" list, which shifts every index after it. Position based lookups will
reply to the wrong customer.

**Skip conditions** (both are normal, neither is an error):
- A visible textarea reading "This retailer doesn't allow responses to reviews."
- A visible `Upgrade to Respond to Reviews` button, meaning the account lacks the entitlement.

**Confirmation:** after clicking Respond, the card either drops out of the filtered list or
gains a "Published by" line. If neither happens, treat the post as failed.

**Rehearsing:** `--rehearse` types each reply into the real editor and then clicks Cancel.
It exercises the whole path except the irreversible final click, which makes it the right
way to check selectors after a Bazaarvoice UI change.

Drafts that fail brand validation are never posted, in any mode.

## Daily run and RingCentral notification (REQUIRED)

**Always send a notification to the RingCentral channel every time the daily run finishes.**
This is not optional and must never be skipped:

- On a completed run, post a **success** notification titled
  `Bazaarvoice review bot ran successfully` with `**Status:** SUCCESS`.
- On a failure, post a **failure** notification with `**Status:** FAILED` and the reason.
- A silent day therefore always means the run never fired, never that a notification was
  skipped. Do not add flags to suppress it for scheduled runs.

The success message reports mode (dry run or live), reviews processed, the breakdown by
review type, drafts flagged by the brand rules, how many were skipped as a year or older,
the inbox counter, the filters used, and the run folder.

The webhook URL lives in `config.json` under `webhook.url` and can be overridden with the
`RINGCENTRAL_WEBHOOK_URL` environment variable.

## Step 6: Cloud Server Deployment

### On Your Cloud Server

**1. Clone and setup:**
```bash
git clone https://github.com/your-username/bazaarvoice-bot.git
cd bazaarvoice-bot
npm install
```

**2. Add credentials (secure method):**
```bash
# Option A: Create credentials.json (not in GitHub)
cat > credentials.json << 'EOF'
{
  "bazaarvoice": {
    "username": "your_email@example.com",
    "password": "your_password",
    "url": "https://response.bazaarvoice.com/#/respond"
  }
}
EOF

# Option B: Use environment variables (if your script supports it)
export BAZAARVOICE_USERNAME="your_email@example.com"
export BAZAARVOICE_PASSWORD="your_password"
```

**3. Run the bot:**
```bash
npm start
```

**4. Schedule on cloud server:**

Using cron (Linux/Mac):
```bash
# Edit crontab
crontab -e

# Add this line to run bot daily at 5 PM.
# The bot posts its own success notification to RingCentral when it finishes.
0 17 * * * cd /path/to/bazaarvoice-bot && node bazaarvoice-bot.js --post
```

Using Windows Task Scheduler:
- Create task with trigger "Daily at 5:00 PM"
- Action: `node "C:\path\to\bazaarvoice-bot\bazaarvoice-bot.js"`

## Step 7: Monitoring and Maintenance

**Check logs:**
```bash
npm start > bot.log 2>&1
tail -f bot.log
```

**Common issues:**
- **Login fails** → Credentials invalid or Bazaarvoice UI changed
- **Selectors don't match** → Inspect page, update selectors in script
- **No reviews found** → Check filters are applied correctly

**Updates:**
- When Bazaarvoice changes UI, update page selectors
- Test locally before deploying changes to server
- Keep credentials.json secure and never commit it

## Security Best Practices

✅ **Do:**
- Store credentials.json only on your server (not in GitHub)
- Use `.gitignore` to prevent accidental commits
- Rotate credentials regularly
- Run bot with minimal required permissions
- Log activity but never log credentials

❌ **Don't:**
- Commit credentials to GitHub
- Store credentials in environment variables in shell history
- Run bot with elevated privileges
- Share credentials.json across machines

## Example Response Patterns

**Positive review:**
> "We're so glad you love your Liquipel product! Thank you!"

**Product defect:**
> "We're sorry the charging cable isn't working properly. We'd like to make this right for you. Please contact our support team at ecom@liquipel.com or call 1 855 478 4735 (Monday to Friday, 8 AM to 5 PM Pacific Time) and they'll send you a replacement right away. Thank you!"

**Charging speed complaint:**
> "Thanks for your feedback on charging speed. Fast charging works best when paired with a compatible fast charging wall adapter and compatible device. Our support team at ecom@liquipel.com or 1 855 478 4735 (Monday to Friday, 8 AM to 5 PM Pacific Time) can help ensure you have the right setup. Thank you!"

## Next Steps

1. Create the files locally
2. Test the bot with your Bazaarvoice account
3. Push to GitHub (credentials excluded)
4. Deploy to cloud server
5. Set up scheduling
6. Monitor logs and iterate

Good luck!
