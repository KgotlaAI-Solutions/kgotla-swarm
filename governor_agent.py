"""
Kgotla AI Intelligence Swarm — Governor Agent
The brain of the swarm. Wakes up on schedule, dispatches sector agents,
synthesises their reports into a single actionable intelligence brief.

Output: JSON brief pushed to Supabase + morning email/WhatsApp digest.
"""

import json
import datetime
from model_router import router, TaskType


GOVERNOR_SYSTEM = """
You are the Chief Intelligence Director of Kgotla AI Consulting — a Black-owned AI 
firm entering South Africa's mining, energy, power, and government sectors.

Your job: review sector agent reports and produce ONE daily intelligence brief.

Always output VALID JSON only. No markdown, no preamble, no explanation outside the JSON.
"""

SYNTHESIS_PROMPT_TEMPLATE = """
Today is {date}. Below are reports from all four sector agents.

=== MINING AGENT REPORT ===
{mining_report}

=== ENERGY AGENT REPORT ===
{energy_report}

=== GOVERNMENT AGENT REPORT ===
{govt_report}

=== ENTERPRISE AGENT REPORT ===
{enterprise_report}

Analyse all four reports and produce a JSON intelligence brief in exactly this structure:
{{
  "date": "{date}",
  "executive_summary": "2-3 sentence overview of today's most critical intelligence",
  "top_opportunities": [
    {{
      "title": "Opportunity name",
      "sector": "mining|energy|government|enterprise",
      "urgency": "critical|high|medium",
      "value_estimate_zar": "estimated rand value e.g. R2.5M",
      "action": "Specific action Kgotla AI must take today",
      "deadline": "YYYY-MM-DD or null"
    }}
  ],
  "top_threats": [
    {{
      "title": "Threat name",
      "sector": "sector name",
      "impact": "What this means for Kgotla AI's pipeline",
      "mitigation": "How to counter it"
    }}
  ],
  "sector_scores": {{
    "mining": "0-10 activity level today",
    "energy": "0-10 activity level today",
    "government": "0-10 activity level today",
    "enterprise": "0-10 activity level today"
  }},
  "recommended_outreach": [
    {{
      "entity": "Company or department name",
      "reason": "Why contact them today",
      "contact_approach": "email|linkedin|phone|tender_portal"
    }}
  ]
}}
"""


class GovernorAgent:

    def __init__(self, sector_agents: dict):
        """
        sector_agents: dict of {sector_name: SectorAgent instance}
        e.g. {"mining": MiningAgent(), "energy": EnergyAgent(), ...}
        """
        self.sector_agents = sector_agents

    def run_daily_brief(self) -> dict:
        """
        Full daily cycle:
        1. Dispatch all sector agents to collect fresh data
        2. Synthesise into one intelligence brief via Governor LLM
        3. Return structured brief dict
        """
        today = datetime.date.today().isoformat()
        print(f"\n[Governor] Starting daily intelligence cycle for {today}")

        # Step 1: Collect sector reports in parallel (sequential for simplicity first)
        sector_reports = {}
        for name, agent in self.sector_agents.items():
            print(f"[Governor] Dispatching {name} agent...")
            try:
                sector_reports[name] = agent.collect()
            except Exception as e:
                sector_reports[name] = f"Agent failed: {str(e)}"
                print(f"[Governor] WARNING: {name} agent failed — {e}")

        # Step 2: Synthesise via LLM (Governor uses Groq for speed)
        synthesis_prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
            date=today,
            mining_report=sector_reports.get("mining", "No data"),
            energy_report=sector_reports.get("energy", "No data"),
            govt_report=sector_reports.get("government", "No data"),
            enterprise_report=sector_reports.get("enterprise", "No data"),
        )

        print("[Governor] Synthesising intelligence brief...")
        response = router.route(
            prompt=synthesis_prompt,
            system=GOVERNOR_SYSTEM,
            task_type=TaskType.REASONING,
            max_tokens=2048
        )

        if not response.success:
            print(f"[Governor] LLM synthesis failed: {response.error}")
            return {"error": response.error, "date": today}

        # Step 3: Parse JSON
        try:
            # Strip any accidental markdown fences
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            brief = json.loads(raw)
            print(f"[Governor] Brief ready. {len(brief.get('top_opportunities', []))} opportunities found.")
            return brief
        except json.JSONDecodeError as e:
            print(f"[Governor] JSON parse error: {e}")
            return {"raw_output": response.content, "date": today, "parse_error": str(e)}

    def format_whatsapp_digest(self, brief: dict) -> str:
        """
        Formats the brief as a WhatsApp-friendly morning message for Mahlo.
        """
        if "error" in brief:
            return f"⚠️ Kgotla AI Swarm error: {brief['error']}"

        lines = [
            f"🔱 *KGOTLA AI INTEL BRIEF — {brief.get('date', 'Today')}*",
            "",
            f"📋 {brief.get('executive_summary', '')}",
            "",
            "🔥 *TOP OPPORTUNITIES:*"
        ]

        for i, opp in enumerate(brief.get("top_opportunities", [])[:3], 1):
            urgency_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(opp.get("urgency"), "⚪")
            lines.append(f"{urgency_icon} {i}. *{opp.get('title')}*")
            lines.append(f"   Sector: {opp.get('sector')} | Value: {opp.get('value_estimate_zar', 'TBD')}")
            lines.append(f"   Action: {opp.get('action')}")

        lines.append("")
        lines.append("⚠️ *THREATS TO WATCH:*")
        for threat in brief.get("top_threats", [])[:2]:
            lines.append(f"• *{threat.get('title')}*: {threat.get('impact')}")

        lines.append("")
        lines.append("📞 *OUTREACH TODAY:*")
        for rec in brief.get("recommended_outreach", [])[:3]:
            lines.append(f"• {rec.get('entity')} — {rec.get('reason')}")

        lines.append("")
        lines.append("_Kgotla AI Intelligence Swarm — kgotlaai.co.za_")

        return "\n".join(lines)
