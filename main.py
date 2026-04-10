"""
Kgotla AI Intelligence Swarm — Main Entry Point

Run manually:      python main.py
Run on Railway:    Set this as the start command. Add a cron job at 06:00 SAST daily.

Required env vars (set in Railway or .env):
  GROQ_API_KEY
  GOOGLE_AI_API_KEY
  HF_API_TOKEN
  SUPABASE_URL          (optional — for database storage)
  SUPABASE_ANON_KEY     (optional)
"""

import json
import os
import datetime

from governor_agent import GovernorAgent
from sector_agents import MiningAgent, EnergyAgent, GovernmentAgent, EnterpriseAgent


def push_to_supabase(brief: dict):
    """
    Stores the daily brief in Supabase free tier.
    Table: intelligence_briefs (id, date, brief_json, created_at)
    """
    url  = os.environ.get("SUPABASE_URL", "")
    key  = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        print("[Main] Supabase not configured — skipping DB push.")
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
    if resp.status_code in (200, 201):
        print("[Main] Brief stored in Supabase.")
    else:
        print(f"[Main] Supabase push failed: {resp.status_code} {resp.text}")


def save_brief_locally(brief: dict):
    """Saves brief as JSON file for local debugging / Cloudflare Worker to serve."""
    os.makedirs("briefs", exist_ok=True)
    filename = f"briefs/{brief.get('date', 'latest')}.json"
    with open(filename, "w") as f:
        json.dump(brief, f, indent=2)
    # Always keep a 'latest.json' for the dashboard
    with open("briefs/latest.json", "w") as f:
        json.dump(brief, f, indent=2)
    print(f"[Main] Brief saved to {filename}")


def main():
    print("=" * 60)
    print("  KGOTLA AI INTELLIGENCE SWARM — DAILY CYCLE")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S SAST')}")
    print("=" * 60)

    # Instantiate all sector agents
    agents = {
        "mining":     MiningAgent(),
        "energy":     EnergyAgent(),
        "government": GovernmentAgent(),
        "enterprise": EnterpriseAgent(),
    }

    # Instantiate and run Governor
    governor = GovernorAgent(sector_agents=agents)
    brief = governor.run_daily_brief()

    # Output
    print("\n" + "─" * 60)
    print("DAILY INTELLIGENCE BRIEF:")
    print(json.dumps(brief, indent=2))
    print("─" * 60)

    # WhatsApp digest
    digest = governor.format_whatsapp_digest(brief)
    print("\nWHATSAPP DIGEST:\n")
    print(digest)

    # Persist
    save_brief_locally(brief)
    push_to_supabase(brief)

    print("\n[Main] Daily cycle complete.")
    return brief


if __name__ == "__main__":
    main()
