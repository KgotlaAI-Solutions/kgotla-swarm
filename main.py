"""
Kgotla AI Intelligence Swarm — Main Entry Point
Run: python main.py
GitHub Actions: runs daily at 06:00 SAST via cron 0 4 * * *
"""

import json
import os
import datetime
import pytz

from governor_agent import GovernorAgent
from sector_agents import MiningAgent, EnergyAgent, GovernmentAgent, EnterpriseAgent


def push_to_supabase(brief: dict):
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        print("[Main] Supabase not configured — skipping.")
        return
    import requests
    resp = requests.post(
        f"{url}/rest/v1/intelligence_briefs",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json={"date": brief.get("date"), "brief_json": json.dumps(brief)}
    )
    print("[Main] Supabase push:", resp.status_code)


def save_brief_locally(brief: dict):
    os.makedirs("briefs", exist_ok=True)
    date_str = brief.get("date", "latest")
    with open(f"briefs/{date_str}.json", "w") as f:
        json.dump(brief, f, indent=2)
    with open("briefs/latest.json", "w") as f:
        json.dump(brief, f, indent=2)
    print(f"[Main] Brief saved: briefs/{date_str}.json")


def main():
    sast        = pytz.timezone("Africa/Johannesburg")
    today_sast  = datetime.datetime.now(sast).strftime("%Y-%m-%d")
    now_str     = datetime.datetime.now(sast).strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 60)
    print("  KGOTLA AI INTELLIGENCE SWARM — DAILY CYCLE")
    print(f"  {now_str} SAST")
    print("=" * 60)

    agents = {
        "mining":     MiningAgent(),
        "energy":     EnergyAgent(),
        "government": GovernmentAgent(),
        "enterprise": EnterpriseAgent(),
    }

    governor = GovernorAgent(sector_agents=agents, today=today_sast)
    brief    = governor.run_daily_brief()

    print("\n" + "─" * 60)
    print("DAILY INTELLIGENCE BRIEF:")
    print(json.dumps(brief, indent=2))
    print("─" * 60)

    print("\nWHATSAPP DIGEST:\n")
    print(governor.format_whatsapp_digest(brief))

    save_brief_locally(brief)
    push_to_supabase(brief)

    print("\n[Main] Daily cycle complete.")
    return brief


if __name__ == "__main__":
    main()
