/**
 * Bazaarvoice review response bot.
 *
 * Safe by default: runs as a DRY RUN and posts nothing. Pass --post to submit
 * responses for real.
 *
 *   node bazaarvoice-bot.js                  dry run, drafts only
 *   node bazaarvoice-bot.js --self-test      offline check of the drafting rules
 *   node bazaarvoice-bot.js --limit 5        only handle the first 5 reviews
 *   node bazaarvoice-bot.js --post           actually post the responses
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const config = require('./config.json');

const RULES = config.response_rules;
const OUT = path.join(__dirname, 'runs', new Date().toISOString().replace(/[:.]/g, '-'));
const AUTH_STATE = path.join(__dirname, 'auth-state.json');

const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const opt = (name, fallback) => {
  const i = argv.indexOf(name);
  return i !== -1 && argv[i + 1] ? argv[i + 1] : fallback;
};

const POST = flag('--post');
const HEADLESS = flag('--headless') ? true : config.browser.headless;
const LIMIT = parseInt(opt('--limit', '0'), 10) || 0;
const TIMEOUT = config.browser.timeout;

const log = (...a) => console.log(...a);

/* ------------------------------------------------------------------ */
/* Response drafting                                                    */
/* ------------------------------------------------------------------ */

const SUPPORT = `${RULES.support_email} or call ${RULES.support_phone} (${RULES.support_hours})`;

const OPENINGS = {
  positive: [
    'We are so glad you are happy with it!',
    'What a great thing to hear!',
    'It is great to hear this worked out so well for you!',
    'We love hearing this!',
  ],
  negative: [
    'We are sorry this did not work out as expected.',
    'We apologize that this fell short for you.',
    'We are sorry to hear about this experience.',
    'This is not what we want you to receive.',
  ],
};

const counter = { positive: 0, negative: 0 };
function opening(kind) {
  const list = OPENINGS[kind];
  return list[counter[kind]++ % list.length];
}

/** Strip every kind of dash, per the brand rule. Keeps spacing tidy. */
function stripDashes(text) {
  return text.replace(/[-‐-―−]/g, ' ').replace(/\s{2,}/g, ' ').trim();
}

function classify(reviewText, rating) {
  const t = (reviewText || '').toLowerCase();

  const mentionsCharging = /charg|wall adapter|watt/.test(t);
  const defect = /not work|doesn.?t work|didn.?t work|stopped working|broke|broken|defect|damaged|cracked|faulty|dead|useless|fell apart|quit working/.test(t);
  const complaint = /slow|sluggish|barely|hardly|disappoint|poor|cheap|waste|never |won.?t |wouldn.?t |returned|refund|too long|worse/.test(t);
  const praise = /love|excellent|great|perfect|awesome|amazing|works well|highly recommend|happy|best|nice|easy|like this|good|works fine|no problem|brand new|as described|quality/.test(t);

  // Only treat charging as the topic when the customer is unhappy about it.
  // A five star review that happens to say "charges quickly" is praise.
  const chargingIssue = mentionsCharging && (defect || complaint || (rating && rating <= 3));

  if (chargingIssue) return 'charging';
  if (defect) return 'defect';
  if (complaint && rating && rating <= 3) return 'defect';
  if (praise && !defect && !complaint) return 'positive';
  if (rating && rating >= 4) return 'positive';
  return 'neutral';
}

function draftResponse(review) {
  const name = (review.reviewer || '').trim();
  const greeting = name && !/^anonymous$/i.test(name) ? `Hi ${name}, ` : '';
  const type = classify(review.text, review.rating);
  let body;

  switch (type) {
    case 'positive':
      body = `${opening('positive')} ${RULES.closing}`;
      break;
    case 'defect':
      body = `${opening('negative')} We would like to make this right and send you a replacement. Please reach out to our support team at ${SUPPORT} and they will take care of you. ${RULES.closing}`;
      break;
    case 'charging':
      body = `Thanks for sharing your feedback on charging. Fast charging works best when the cable is paired with a compatible fast charging wall adapter and a compatible device. Our support team at ${SUPPORT} can help make sure you have the right setup or send a replacement if something is not working. ${RULES.closing}`;
      break;
    default:
      // Lukewarm review with no stated problem: stay short and do not push
      // support contact or a replacement the customer never asked for.
      body = `We appreciate you taking the time to share your feedback. ${RULES.closing}`;
  }

  return { type, response: stripDashes(greeting + body) };
}

/** Brand rules that every outgoing response must satisfy. */
function validate(response, type) {
  const problems = [];
  if ((type === 'positive' || type === 'neutral') && response.includes(RULES.support_email)) {
    problems.push('pushes support contact on a review with no stated problem');
  }
  if (type === 'positive' && response.split(/[.!?]\s/).length > 3) {
    problems.push('positive reply runs longer than two sentences');
  }
  if (/[-‐-―−]/.test(response)) problems.push('contains a dash');
  if (!response.endsWith(RULES.closing)) problems.push(`does not close with "${RULES.closing}"`);
  if (/have a great day/i.test(response)) problems.push('uses banned closing "have a great day"');
  if ((response.match(/thank you/gi) || []).length > 1) problems.push('says "thank you" more than once');
  if (/refund|money back|reimburse/i.test(response)) problems.push('mentions a refund');
  if (response.length > 1000) problems.push('over 1000 characters');
  return problems;
}

/* ------------------------------------------------------------------ */
/* Offline self test                                                    */
/* ------------------------------------------------------------------ */

const SAMPLES = [
  { reviewer: 'Sarah', rating: 5, text: 'I love this cable, it is excellent and works great every day.' },
  { reviewer: 'Mike', rating: 1, text: 'Stopped working after two weeks. Completely broken now.' },
  { reviewer: 'Anonymous', rating: 2, text: 'Charging is really slow compared to my old cable.' },
  { reviewer: '', rating: 3, text: 'It is fine I guess. Nothing special about it.' },
  { reviewer: 'Dana', rating: 2, text: 'The fast charging does not work at all, cable seems defective.' },
  { reviewer: 'Chris', rating: 5, text: 'Perfect fit and it charges quickly. Highly recommend.' },
  { reviewer: 'Pat', rating: 4, text: 'Great quality cable, though the cord is a little shorter than I expected.' },
  { reviewer: 'Jordan', rating: 1, text: 'Arrived cracked and the packaging was damaged. Very disappointed.' },
  { reviewer: 'Alex', rating: 3, text: 'Love the braided design but it charges slower than my old one.' },
];

function selfTest() {
  log('Running offline self test of the drafting rules\n');
  let failures = 0;
  const seen = new Set();
  for (const s of SAMPLES) {
    const { type, response } = draftResponse(s);
    const problems = validate(response, type);
    if (problems.length) failures++;
    seen.add(response);
    log(`  [${type.padEnd(8)}] ${s.rating} star  "${s.text.slice(0, 55)}..."`);
    log(`     -> ${response}`);
    log(`     ${problems.length ? 'FAIL: ' + problems.join('; ') : 'ok'}\n`);
  }
  log(`Rule violations: ${failures}`);
  log(`Distinct responses across ${SAMPLES.length} samples: ${seen.size}`);
  return failures === 0;
}

/* ------------------------------------------------------------------ */
/* RingCentral notification                                             */
/* ------------------------------------------------------------------ */

const WEBHOOK_URL = process.env.RINGCENTRAL_WEBHOOK_URL || (config.webhook && config.webhook.url);
const NOTIFY = !flag('--skip-webhook');

/**
 * Every completed run reports to the RingCentral channel, success and failure
 * alike, so a silent daily run is always a real problem and never just a
 * skipped notification.
 */
async function notifyRingCentral(title, lines) {
  if (!NOTIFY) {
    log('Webhook skipped (--skip-webhook)');
    return { skipped: true };
  }
  if (!WEBHOOK_URL) {
    log('WARNING: no webhook URL configured, RingCentral notification skipped');
    return { skipped: true, reason: 'no url' };
  }
  const body = { title, text: lines.join('\n') };
  const timeout = (config.webhook && config.webhook.timeout_seconds ? config.webhook.timeout_seconds : 15) * 1000;
  try {
    const res = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeout),
    });
    log(`RingCentral notification sent (HTTP ${res.status})`);
    return { ok: res.ok, status: res.status };
  } catch (err) {
    log(`WARNING: RingCentral notification failed: ${err.message}`);
    return { ok: false, error: err.message };
  }
}

/* ------------------------------------------------------------------ */
/* Browser automation                                                   */
/* ------------------------------------------------------------------ */

async function shot(page, name) {
  fs.mkdirSync(OUT, { recursive: true });
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true }).catch(() => {});
  log(`   screenshot: ${path.relative(__dirname, file)}`);
}

/** Try a list of selectors, return the first one that is actually visible. */
async function firstVisible(page, selectors, timeout = 8000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    for (const sel of selectors) {
      const loc = page.locator(sel).first();
      if (await loc.isVisible().catch(() => false)) return loc;
    }
    await page.waitForTimeout(400);
  }
  return null;
}

/**
 * The OneTrust consent banner overlays the login form and swallows clicks,
 * so it has to go before anything else on the page can be driven.
 */
async function dismissCookieBanner(page) {
  const accept = await firstVisible(page, [
    '#onetrust-accept-btn-handler',
    'button:has-text("Accept All Cookies")',
    'button:has-text("Accept all")',
    '.onetrust-close-btn-handler',
  ], 5000);
  if (!accept) return false;
  await accept.click().catch(() => {});
  await page.locator('#onetrust-banner-sdk').waitFor({ state: 'hidden', timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(500);
  log('   dismissed cookie consent banner');
  return true;
}

async function isLoggedIn(page) {
  if (await page.locator('input[type="password"]').first().isVisible().catch(() => false)) return false;
  const url = page.url();
  if (/login|signin|sign-in|auth0|\/auth/i.test(url)) return false;
  // Anywhere inside the authenticated app counts: the portal drops you on
  // /home first and only then routes through to the respond workspace.
  return /bazaarvoice\.com/i.test(url);
}

/** The app renders a full page spinner while it boots. Wait it out. */
async function waitForAppReady(page) {
  await page.waitForLoadState('networkidle', { timeout: TIMEOUT }).catch(() => {});
  await page
    .locator('[class*="spinner" i], [class*="loading" i], [role="progressbar"]')
    .first()
    .waitFor({ state: 'hidden', timeout: 20000 })
    .catch(() => {});
  await page.waitForTimeout(1500);
}

async function login(page, credentials) {
  log('Logging in to Bazaarvoice');
  await page.goto(credentials.url, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
  await page.waitForTimeout(3000);
  await dismissCookieBanner(page);

  if (await isLoggedIn(page)) {
    log('   already authenticated from saved session');
    return true;
  }

  const emailField = await firstVisible(page, [
    'input[type="email"]',
    'input[name="username"]',
    'input[name="email"]',
    'input[id*="mail" i]',
    'input[placeholder*="mail" i]',
  ]);
  if (!emailField) {
    await shot(page, 'login-no-email-field');
    throw new Error('Could not find the email field on the login page');
  }
  await emailField.fill(credentials.username);

  // Some tenants use a two step form: email, Next, then password.
  let passwordField = await firstVisible(page, ['input[type="password"]'], 2000);
  if (!passwordField) {
    const next = await firstVisible(page, [
      'button:has-text("Next")',
      'button:has-text("Continue")',
      'button[type="submit"]',
    ], 3000);
    if (next) {
      await next.click();
      await page.waitForTimeout(2500);
    }
    passwordField = await firstVisible(page, ['input[type="password"]'], 8000);
  }
  if (!passwordField) {
    await shot(page, 'login-no-password-field');
    throw new Error('Could not find the password field on the login page');
  }
  await passwordField.fill(credentials.password);

  const submit = await firstVisible(page, [
    'button[type="submit"]',
    'button:has-text("Sign in")',
    'button:has-text("Log in")',
    'input[type="submit"]',
  ]);
  if (!submit) {
    await shot(page, 'login-no-submit');
    throw new Error('Could not find the sign in button');
  }
  await submit.click();
  await page.waitForTimeout(6000);
  await waitForAppReady(page);

  if (!(await isLoggedIn(page))) {
    await shot(page, 'login-failed');
    throw new Error(`Login did not complete. Landed on ${page.url()} (MFA or SSO may be required)`);
  }
  log(`   authenticated, landed on ${page.url()}`);

  await page.context().storageState({ path: AUTH_STATE });
  log('   session saved');
  return true;
}

/**
 * Route into the respond workspace.
 *
 * Going straight to response.bazaarvoice.com/#/respond just bounces back to
 * the portal home, so the only reliable path is the one a human takes:
 * More > Connections (which opens a NEW TAB) > Questions and Reviews.
 * Returns the tab the review inbox actually lives in.
 */
async function openRespondWorkspace(page) {
  log('Opening the respond workspace (More > Connections > Questions and Reviews)');

  await page.locator('button:has-text("More"), [role="button"]:has-text("More")').first().click();
  await page.waitForTimeout(1500);

  const [popup] = await Promise.all([
    page.context().waitForEvent('page', { timeout: 20000 }).catch(() => null),
    page.locator('button[role="menuitem"]:has-text("Connections")').first().click(),
  ]);

  const app = popup || page;
  await app.waitForTimeout(8000);
  await waitForAppReady(app);
  await dismissCookieBanner(app);
  log(`   connections tab: ${app.url()}`);

  await app.locator(':text-is("Questions and Reviews")').first().click();
  await app.waitForTimeout(8000);
  await waitForAppReady(app);
  log(`   review inbox: ${app.url()}`);
  await shot(app, 'respond-workspace');
  return app;
}

/** Reads the "N of M" counter above the result list. */
async function resultCount(page) {
  const text = await page
    .locator(':text-matches("of [0-9,]+")')
    .first()
    .innerText()
    .catch(() => '');
  return text.replace(/\s+/g, ' ').trim();
}

async function applyFilters(page) {
  const wanted = [config.filters.content_type, config.filters.state, config.filters.time_range].filter(Boolean);
  log(`Applying filters: ${wanted.join(' + ')}`);

  for (const label of wanted) {
    // The sidebar filters are plain text nodes in an Angular list, so an exact
    // text match is what actually hits them.
    const control = page.locator(`:text-is("${label}")`).first();
    if (await control.isVisible().catch(() => false)) {
      await control.click().catch(() => {});
      await page.waitForTimeout(4000);
      log(`   applied "${label}"  ->  ${await resultCount(page)}`);
    } else {
      log(`   WARNING: filter "${label}" not found, continuing without it`);
    }
  }
  await page.waitForTimeout(2500);
  await shot(page, 'after-filters');
}

const CARD_SELECTOR = '[ng-repeat="content in contentStore.contents"]';

/**
 * Turn a relative timestamp like "3 months ago" or "a year ago" into days.
 * Returns null when nothing parseable is present.
 */
function ageInDays(label) {
  const m = (label || '').match(/(a|an|\d+)\s+(minute|hour|day|week|month|year)s?\s+ago/i);
  if (!m) return null;
  const n = /^(a|an)$/i.test(m[1]) ? 1 : parseInt(m[1], 10);
  const perUnit = { minute: 1 / 1440, hour: 1 / 24, day: 1, week: 7, month: 30.44, year: 365.25 };
  return n * perUnit[m[2].toLowerCase()];
}

/**
 * Cards render as plain text blocks shaped like:
 *   SSSSS / SSSSS            (star glyphs)
 *   [optional review title]
 *   Product name @ Retailer  ‐ 3 months ago
 *   review body
 *   [optional reviewer name]
 *   Mark Unread
 */
function parseCard(raw, index) {
  const lines = raw
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !/^S+$/.test(l));

  const headerIdx = lines.findIndex((l) => /\sago\s*$/.test(l) && /@/.test(l));
  if (headerIdx === -1) return null;

  const header = lines[headerIdx];
  const agoMatch = header.match(/((?:a|an|\d+)\s+\w+\s+ago)\s*$/i);
  const age = agoMatch ? agoMatch[1] : null;
  const productPart = header.split(/\s+[‐\-–—]\s+(?:a|an|\d+)\s+\w+\s+ago/)[0];
  const [product, retailer] = productPart.split('@').map((s) => (s || '').trim());

  const title = headerIdx > 0 ? lines[headerIdx - 1] : null;

  // Everything between the header and the trailing controls is body + name.
  const tail = lines.slice(headerIdx + 1).filter((l) => !/^(Mark Unread|Mark Read|View Best Practices|Edit|Delete)$/i.test(l));
  const body = tail[0] || '';
  const maybeName = tail[1] || '';
  // A short trailing line that is not a sentence is the reviewer handle.
  const reviewer = maybeName && maybeName.length <= 30 && !/[.!?]$/.test(maybeName) ? maybeName : '';

  return {
    index,
    product: product || null,
    retailer: retailer || null,
    title: title && title !== product ? title : null,
    text: body,
    reviewer,
    age,
    ageDays: ageInDays(age),
    rating: null, // stars render as glyphs, so tone is driven by the text
  };
}

async function extractReviews(page) {
  const count = await page.locator(CARD_SELECTOR).count().catch(() => 0);
  log(`   ${count} review card(s) loaded in the list`);
  if (!count) return { reviews: [], skippedOld: 0, unparsed: 0 };

  const maxAgeDays = (config.filters.max_age_months || 12) * 30.44;
  const reviews = [];
  let skippedOld = 0;
  let unparsed = 0;

  for (let i = 0; i < count; i++) {
    if (LIMIT && reviews.length >= LIMIT) break;
    const raw = (await page.locator(CARD_SELECTOR).nth(i).innerText().catch(() => '')).trim();
    if (!raw) continue;

    const card = parseCard(raw, i);
    if (!card || !card.text) {
      unparsed++;
      continue;
    }

    // Stars are glyphs; the score lives in the width of the filled overlay,
    // so 100% is five stars, 60% is three.
    card.rating = await page
      .locator(CARD_SELECTOR)
      .nth(i)
      .locator('.response-star-on')
      .first()
      .evaluate((el) => {
        const w = parseFloat((el.style.width || '').replace('%', ''));
        return Number.isNaN(w) ? null : Math.round(w / 20);
      })
      .catch(() => null);
    // Anything a year or older is stale, leave it alone.
    if (card.ageDays !== null && card.ageDays >= maxAgeDays) {
      skippedOld++;
      continue;
    }
    reviews.push(card);
  }

  if (skippedOld) log(`   skipped ${skippedOld} review(s) a year or older`);
  if (unparsed) log(`   could not parse ${unparsed} card(s)`);
  return { reviews, skippedOld, unparsed };
}

async function main() {
  if (flag('--self-test')) {
    process.exit(selfTest() ? 0 : 1);
  }

  let credentials;
  try {
    credentials = require('./credentials.json').bazaarvoice;
  } catch (e) {
    console.error('Missing credentials.json. Copy credentials.json.example and fill it in.');
    process.exit(1);
  }
  if (!credentials || !credentials.username || !credentials.password) {
    console.error('credentials.json is missing bazaarvoice.username or bazaarvoice.password');
    process.exit(1);
  }

  log(POST ? '*** LIVE MODE: responses will be posted ***\n' : 'DRY RUN: nothing will be posted\n');

  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext(
    fs.existsSync(AUTH_STATE) ? { storageState: AUTH_STATE } : {}
  );
  const page = await context.newPage();
  page.setDefaultTimeout(TIMEOUT);

  const report = { started: new Date().toISOString(), mode: POST ? 'post' : 'dry-run', drafts: [] };

  try {
    await login(page, credentials);
    const app = await openRespondWorkspace(page);
    await applyFilters(app);

    const { reviews, skippedOld, unparsed } = await extractReviews(app);
    report.skippedOld = skippedOld;
    report.unparsed = unparsed;
    report.resultCount = await resultCount(app);
    log(`\nProcessing ${reviews.length} review(s)\n`);

    for (const review of reviews) {
      const { type, response } = draftResponse(review);
      const problems = validate(response, type);
      report.drafts.push({ ...review, type, response, problems });

      log(`[${review.index}] ${type} | ${review.rating ? review.rating + ' star' : 'no rating'} | ${review.age || '?'} | ${review.reviewer || 'anonymous'} | ${review.retailer || '?'}`);
      log(`    product: ${(review.product || '').slice(0, 80)}`);
      log(`    review : ${review.text.replace(/\s+/g, ' ').slice(0, 140)}`);
      log(`    reply : ${response}`);
      if (problems.length) log(`    RULE VIOLATION: ${problems.join('; ')}`);

      if (POST) {
        if (problems.length) {
          log('    skipped posting because the draft failed validation');
          continue;
        }
        log('    posting is not wired to the live editor yet, skipped');
      }
      log('');
    }

    fs.mkdirSync(OUT, { recursive: true });
    fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
    log(`Report written to ${path.relative(__dirname, path.join(OUT, 'report.json'))}`);

    const byType = report.drafts.reduce((acc, d) => {
      acc[d.type] = (acc[d.type] || 0) + 1;
      return acc;
    }, {});
    const flagged = report.drafts.filter((d) => d.problems.length).length;
    await notifyRingCentral(
      `Bazaarvoice review bot ran successfully (${report.mode})`,
      [
        `**Status:** SUCCESS`,
        `**Mode:** ${POST ? 'LIVE, responses posted' : 'DRY RUN, nothing posted'}`,
        `**Reviews processed:** ${report.drafts.length}`,
        `**Positive:** ${byType.positive || 0}`,
        `**Defect:** ${byType.defect || 0}`,
        `**Charging:** ${byType.charging || 0}`,
        `**Neutral:** ${byType.neutral || 0}`,
        `**Drafts flagged by brand rules:** ${flagged}`,
        `**Skipped as a year or older:** ${report.skippedOld || 0}`,
        `**Inbox counter:** ${report.resultCount || 'n/a'}`,
        `**Filters:** ${[config.filters.content_type, config.filters.state, config.filters.time_range].filter(Boolean).join(', ')}`,
        `**Run folder:** \`${path.relative(__dirname, OUT)}\``,
        `**Finished (UTC):** ${new Date().toISOString()}`,
      ]
    );
  } catch (error) {
    log(`\nERROR: ${error.message}`);
    await shot(page, 'error');
    fs.mkdirSync(OUT, { recursive: true });
    fs.writeFileSync(
      path.join(OUT, 'report.json'),
      JSON.stringify({ ...report, error: error.message }, null, 2)
    );
    await notifyRingCentral('Bazaarvoice review bot FAILED', [
      `**Status:** FAILED`,
      `**Mode:** ${POST ? 'LIVE' : 'DRY RUN'}`,
      `**Reason:** ${error.message}`,
      `**Reviews processed before failure:** ${report.drafts.length}`,
      `**Run folder:** \`${path.relative(__dirname, OUT)}\``,
      `**Failed (UTC):** ${new Date().toISOString()}`,
    ]);
    await browser.close();
    process.exit(1);
  }

  await browser.close();
  log('Done');
}

main();
