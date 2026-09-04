# Schedule and account

Additions to Sarah's bot. The bot itself, its drafting rules and its CLI are hers and are
documented in `SETUP-INSTRUCTIONS.md` and `bazaarvoice-automation-SKILL.md`. This file covers
only the two things that were missing: **when it runs** and **which account it runs as**.

## Account

| | |
|---|---|
| Login | `shamilton@liquipel.com` (in `credentials.json`, git ignored) |
| Portal user | Steven Hamilton |
| Client | **Liquipel** |
| Replies publish as | **Liquipel Assistance** |
| Retailers in the inbox | Walmart, BestBuy, Target, The Home Depot, Sam's Club, The Source |
| MFA / SSO | none on this account today, so unattended login works |

The login carries three Bazaarvoice clients. **Connections is entitled under `Liquipel` only**:

| Client | Active services | Has the review inbox |
|---|---|---|
| `Liquipel` | connections, workbench, portal-reports | **yes** |
| `liquipelprotection` | platform-config, cv2, workbench, sampling, manage-content, portal-reports, curalate | no |
| `SimpleEvidentClean` | connections, portal-reports, workbench | not used |

`liquipelprotection` looks like the better candidate at first glance because it holds the
content permissions (`CONTENT:NATIVE_REVIEW_RESPOND`), but the portal assets granted to this
user are only `CONNECTIONS, REPORTS, SAMPLING, CURALATE`. Without the `MANAGE_CONTENT_RR` asset
its `/ratingsandreviews` route redirects straight back to `/home` and its nav has no Reviews
app. **Do not switch clients to chase those permissions.** `Liquipel` is the correct one, and it
is what the bot lands on by default, so no client switching is needed.

If that ever changes, the client shown in the header lives in `sessionStorage.selectedClient`
and resets on every full page load, so it has to be seeded in an init script rather than set
once.

## Schedule

Installed in the user crontab:

```
CRON_TZ=America/Los_Angeles
0 17 * * * /home/farsheed/pm-instaprotek/bazaarvoice-bot/run-daily.sh
```

`CRON_TZ` is `America/Los_Angeles` rather than a fixed PST offset, so the job stays at 5:00pm
Pacific across daylight saving. The machine's own clock is Phoenix time, which never shifts, so
without this the run would drift by an hour half the year.

Check it with `crontab -l`. Logs land in `logs/YYYY-MM-DD.log`; the bot's own per run folder in
`runs/` keeps `report.json` and screenshots. Both are pruned after 30 days.

### What the wrapper passes, and why

`run-daily.sh` calls the bot with `--post --headless --limit 25`.

- `--post` because the bot is dry run by default. Without it the cron would draft every night
  and publish nothing.
- `--headless` because `config.json` sets `headless: false` for desktop use and cron has no
  display.
- `--limit 25` because **the backlog is 864 unanswered reviews out of 2,821**, and the bot has
  no built in cap of its own. An uncapped run would publish every card it has loaded, around 50
  public replies, on the first night. 25 a day works the backlog down at a reviewable pace and
  keeps any drafting problem to a small blast radius.

Change the pace without editing the crontab by setting `BV_DAILY_LIMIT`, or run it by hand:

```bash
./run-daily.sh --rehearse          # types each reply then cancels, publishes nothing
BV_DAILY_LIMIT=50 ./run-daily.sh   # bigger catch up run
```

Flags given to `run-daily.sh` are forwarded to the bot and override the defaults above.

### Before the first live night

The publish path has not yet run against a live card here; every check so far was a dry run.
Worth doing once, in this order:

```bash
node bazaarvoice-bot.js --headless --rehearse --limit 1   # types and cancels
node bazaarvoice-bot.js --headless --post --limit 1       # one real reply, then check it
```

Replies are public on the retailer's site. The response app has Edit and Delete per reply, and
a deletion can take up to an hour to propagate.

## Model and token usage

**The scheduled process uses no model at all.** Login, filtering, scraping, drafting, posting
and the RingCentral summary are all Playwright or string formatting; Sarah's `draftResponse()`
is template substitution. The bot's only dependency is `playwright` and its only outbound call
is the webhook. Token cost of a nightly run is zero, so there is nothing to right-size.

This section exists for one reason: if reply drafting is ever moved to a model, the flags below
are not optional. Measured on 2026-09-04, per reply, steady state with a warm cache:

| Configuration | Input tokens | Cost per reply | 864 review backlog |
|---|---|---|---|
| Templates (today) | 0 | $0 | $0 |
| `claude -p` sonnet, no flags | 22,870 | $0.0353 | $30.50 |
| `claude -p` sonnet `--restricted --strict-mcp-config` | 14,434 | $0.0182 | $15.72 |
| `claude -p` haiku 4.5, same flags | 11,022 | $0.0089 | $7.69 |

Roughly 11,000 tokens of every call is Claude Code's own harness: tool definitions, the
Atlassian MCP server's tools, and `CLAUDE.md`, all reloaded to produce an 80 token reply.
`--strict-mcp-config` alone saves about 8,400 tokens per call by not starting MCP servers the
drafter would never use, and `--restricted` drops the tools that run commands, which a
text-only call has no business holding anyway.

So: **haiku 4.5 with `--restricted --strict-mcp-config`**, which is the cheap mechanical end of
the model-to-task rule in `CLAUDE.md`. Drafting a review reply against fixed brand rules is
mechanical work; it does not need a frontier model.

Even optimized that is 99% overhead. The genuinely token-efficient route for this one task is
the Anthropic API with Haiku directly, around 700 tokens per call with no harness, but that
needs an API key rather than the subscription login. At 25 replies a day the difference is
cents, so it is only worth revisiting for a large backlog burn.
