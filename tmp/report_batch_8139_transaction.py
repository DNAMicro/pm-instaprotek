"""Post the final success webhook for batch 8139 — transaction generated."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
settings = json.loads(
    (PROJECT_ROOT / ".claude/skills/instaprotek-enterprise-registration/config/settings.json").read_text()
)

webhook_url = settings["webhook"]["url"]
crm_url = settings["crm"]["base_url"]
run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")

body = {
    "title": "InstaProtek registration COMPLETED — PO 42047 / Batch 8139",
    "text": "\n".join([
        "**Status:** Transaction successfully generated",
        "**Company:** Demo Company",
        "**Plan:** Extended Service Contract - 12 Months",
        "**Product:** Accidental Damage Replacement - 12 Months (ESC030012MO00IK)",
        "**Batch:** 8139",
        "**Pins used:** 20 / 20",
        "**PO Number:** 42047",
        "**Plan Purchase Date:** 05/11/2026",
        "**Expiration Date:** 06/01/2028",
        "**Transaction Date:** 05/15/2026",
        "**Effective Date:** 05/15/2026",
        f"**CRM:** {crm_url}",
        f"**Run timestamp (UTC):** {run_ts}",
    ]),
}

print("Posting:", json.dumps(body, indent=2))
r = requests.post(webhook_url, json=body, timeout=15)
print(f"HTTP {r.status_code}: {r.text[:500]}")
sys.exit(0 if r.ok else 1)
