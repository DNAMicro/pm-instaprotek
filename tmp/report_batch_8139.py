"""One-off: post a success webhook to RingCentral for PO 42047 / Batch 8139.

The registration was completed in the CRM (operator verified Batch 8139). The automation
got the batch created end-to-end and uploaded the CSV; the operator confirmed via the UI.
This script just posts the success notification.
"""
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
    "title": "InstaProtek registration submitted — PO 42047",
    "text": "\n".join([
        "**Company:** Demo Company",
        "**Plan:** Extended Service Contract - 12 Months",
        "**Product:** Accidental Damage Replacement - 12 Months (ESC030012MO00IK)",
        "**Pins:** 20",
        "**Batch:** 8139",
        f"**CRM:** {crm_url}",
        f"**Run timestamp (UTC):** {run_ts}",
    ]),
}

print("Posting:", json.dumps(body, indent=2))
r = requests.post(webhook_url, json=body, timeout=15)
print(f"HTTP {r.status_code}: {r.text[:500]}")
sys.exit(0 if r.ok else 1)
