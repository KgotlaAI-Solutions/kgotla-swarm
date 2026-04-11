"""
Kgotla AI Intelligence Swarm — Governor Agent
Orchestrates all sector agents and produces the daily intelligence brief.
"""

import json
import datetime
import pytz
from model_router import router, TaskType


GOVERNOR_SYSTEM = """
You are the Chief Intelligence Director of Kgotla AI Consulting — a Black-owned AI
firm entering South Africa's mining, energy, power, and government sectors.

Your job: review sector agent reports and produce ONE daily intelligence brief.

Always output VALID JSON only. No markdown, no preamble, no explanation outside the JSON.
Use today's actual date for all deadlines — never use past dates.
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

Produce a JSON intelligence brief in exactly this structure:
{{
  "date": "{date}",
  "executive_summary": "2-3 sentence overview of today's most critical intelligence",
  "top_opportunities": [
    {{
      "title": "Opportunity name",
      "sector": "mining|energy|government|enterprise",
      "urgency": "critical|high|medium",
      "value_estimate_zar": "e.g. R2.5M",
      "action": "Specific action Kgotla AI must take today",
      "deadline": "YYYY-MM-DD or null — must be a future date from {date}"
    }}
  ],
  "top_threats": [
    {{
      "title": "Threat name",
      "sector": "sector name",
      "impact": "What this means for Kgotla AI pipeline",
      "mitigation": "How to counter it"
    }}
  ],
  "sector_scores": {{
    "mining": "0-10",
    "energy": "0-10",
    "government": "0-10",
    "enterprise": "0-10"
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

    def __init__(self, sector_agents: dict, today: str = None):
        self.sector_agents = sector_agents
        if today:
            self.today = today
        else:
            sast = pytz.timezone("Africa/Johannesburg")
            self.today = datetime.datetime.now(sast).strftime("%Y-%m-%d")

    def run_daily_brief(self) -> dict:
        print(f"\n[Governor] Starting daily intelligence cycle for {self.today}")

        sector_reports = {}
        for name, agent in self.sector_agents.items():
            print(f"[Governor] Dispatching {name} agent...")
            try:
                sector_reports[name] = agent.collect()
            except Exception as e:
                sector_reports[name] = f"Agent failed: {str(e)}"
                print(f"[Governor] WARNING: {name} agent failed — {e}")

        synthesis_prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
            date=self.today,
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
            return {"error": response.error, "date": self.today}

        try:
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            brief = json.loads(raw)
            brief["date"] = self.today  # Always force correct SAST date
            print(f"[Governor] Brief ready. {len(brief.get('top_opportunities', []))} opportunities found.")
            return brief
        except json.JSONDecodeError as e:
            print(f"[Governor] JSON parse error: {e}")
            return {"raw_output": response.content, "date": self.today, "parse_error": str(e)}

    def format_whatsapp_digest(self, brief: dict) -> str:
        if "error" in brief:
            return f"⚠️ Kgotla AI Swarm error: {brief['error']}"

        lines = [
            f"🔱 *KGOTLA AI INTEL — {brief.get('date', 'Today')}*",
            "",
            f"📋 {brief.get('executive_summary', '')}",
            "",
            "🔥 *OPPORTUNITIES:*"
        ]
        for i, opp in enumerate(brief.get("top_opportunities", [])[:3], 1):
            icon = {"critical":"🔴","high":"🟠","medium":"🟡"}.get(opp.get("urgency"),"⚪")
            lines.append(f"{icon} {i}. *{opp.get('title')}*")
            lines.append(f"   {opp.get('sector')} | {opp.get('value_estimate_zar','TBD')}")
            lines.append(f"   ↳ {opp.get('action')}")

        lines += ["", "⚠️ *THREATS:*"]
        for t in brief.get("top_threats", [])[:2]:
            lines.append(f"• *{t.get('title')}*: {t.get('impact')}")

        lines += ["", "📞 *OUTREACH TODAY:*"]
        for r in brief.get("recommended_outreach", [])[:3]:
            lines.append(f"• {r.get('entity')} — {r.get('reason')}")

        lines += ["", "_kgotlaai.co.za_"]
        return "\n".join(lines)
