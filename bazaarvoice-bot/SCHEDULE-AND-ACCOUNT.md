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
