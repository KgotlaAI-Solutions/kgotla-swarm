"""
Kgotla AI Intelligence Swarm — Sector Agents
Four specialised agents that collect and analyse sector-specific intelligence.

Each agent:
  1. Hits its assigned data sources (RSS, scraping, APIs)
  2. Passes raw data to the Model Router for extraction/summarisation
  3. Returns a structured text report to the Governor Agent

POPIA NOTE: These agents only collect publicly available data.
No personal information is stored. All data relates to companies,
tenders, and regulatory notices — not individuals.
"""

import re
import requests
import xml.etree.ElementTree as ET
from model_router import router, TaskType


# ─────────────────────────────────────────────
# BASE SECTOR AGENT
# ─────────────────────────────────────────────

class SectorAgent:
    name = "Base"
    sources = []

    def collect(self) -> str:
        """Override in subclasses. Returns a plain-text sector report."""
        raise NotImplementedError

    def _fetch_rss(self, url: str, max_items: int = 10) -> list[dict]:
        """Fetches an RSS feed and returns a list of {title, link, summary} dicts."""
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "KgotlaAI/1.0"})
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            items = []
            for item in root.findall(".//item")[:max_items]:
                items.append({
                    "title":   (item.findtext("title") or "").strip(),
                    "link":    (item.findtext("link") or "").strip(),
                    "summary": (item.findtext("description") or "")[:500].strip(),
                })
            return items
        except Exception as e:
            return [{"title": f"RSS fetch failed: {e}", "link": "", "summary": ""}]

    def _fetch_page_text(self, url: str, max_chars: int = 8000) -> str:
        """Fetches a webpage and returns its text content."""
        try:
            resp = requests.get(
                url, timeout=20,
                headers={"User-Agent": "KgotlaAI/1.0 (+https://kgotlaai.co.za)"}
            )
            resp.raise_for_status()
            # Very simple tag stripper — no extra dependencies needed
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:max_chars]
        except Exception as e:
            return f"Page fetch failed: {e}"

    def _extract_intelligence(self, raw_text: str, focus: str) -> str:
        """Uses the model router to extract actionable intelligence from raw text."""
        prompt = f"""
Extract actionable business intelligence relevant to an AI consulting firm 
entering the South African {focus} sector.

Focus on:
- Open tenders, RFPs, procurement notices
- Budget announcements or spending plans
- Technology upgrade projects
- Regulatory changes that create AI opportunity
- Key company announcements (expansions, partnerships, crises)

Raw data:
{raw_text[:6000]}

Respond in plain text with 3–5 bullet points. Be specific — include company names,
rand values, and deadlines where visible.
"""
        response = router.route(prompt=prompt, task_type=TaskType.EXTRACTION, max_tokens=800)
        return response.content if response.success else f"Extraction failed: {response.error}"


# ─────────────────────────────────────────────
# 1. MINING AGENT
# ─────────────────────────────────────────────

class MiningAgent(SectorAgent):
    name = "Mining"

    # Key SA mining entities Kgotla AI targets
    TARGET_ENTITIES = [
        "Sibanye-Stillwater", "Anglo American Platinum", "Impala Platinum",
        "Northam Platinum", "Harmony Gold", "Gold Fields", "AngloGold Ashanti",
        "Palabora Mining", "Kumba Iron Ore", "Exxaro Resources",
        "Mineral Resources and Energy (DMRE)", "Council for Geoscience"
    ]

    SOURCES = [
        "https://www.miningmx.com/feed/",
        "https://www.engineeringnews.co.za/rss/mining.rss",
        "https://www.southafrica.info/business/economy/sectors/mining.htm",
    ]

    def collect(self) -> str:
        all_text = []

        for url in self.SOURCES:
            items = self._fetch_rss(url, max_items=8)
            for item in items:
                all_text.append(f"HEADLINE: {item['title']}\nSUMMARY: {item['summary']}")

        raw = "\n\n".join(all_text) if all_text else "No mining news retrieved."
        intel = self._extract_intelligence(raw, "mining")

        return f"""
MINING SECTOR INTELLIGENCE REPORT
Targets: {', '.join(self.TARGET_ENTITIES[:6])}...

{intel}

Key Question: Which mines are undergoing digitalisation, automation, 
or compliance-driven IT upgrades right now?
""".strip()


# ─────────────────────────────────────────────
# 2. ENERGY AGENT
# ─────────────────────────────────────────────

class EnergyAgent(SectorAgent):
    name = "Energy"

    TARGET_ENTITIES = [
        "Eskom", "Rand Water", "Umgeni Water", "Lepelle Northern Water",
        "NERSA", "Department of Water and Sanitation (DWS)",
        "IPP Office", "South African National Energy Development Institute (SANEDI)",
        "City Power Johannesburg", "Tshwane Metro Electricity"
    ]

    SOURCES = [
        "https://www.engineeringnews.co.za/rss/energy.rss",
        "https://www.dailymaverick.co.za/rss/",
        "https://www.eskom.co.za/news/",
    ]

    def collect(self) -> str:
        all_text = []

        for url in self.SOURCES:
            items = self._fetch_rss(url, max_items=8)
            for item in items:
                if any(kw in item["title"].lower() for kw in
                       ["eskom", "energy", "power", "water", "nersa", "solar", "load", "grid"]):
                    all_text.append(f"HEADLINE: {item['title']}\nSUMMARY: {item['summary']}")

        # Also check NERSA public notices page
        nersa_text = self._fetch_page_text("https://www.nersa.org.za/applications/", max_chars=4000)
        all_text.append(f"NERSA PORTAL: {nersa_text}")

        raw = "\n\n".join(all_text) if all_text else "No energy news retrieved."
        intel = self._extract_intelligence(raw, "energy and water utilities")

        return f"""
ENERGY & WATER SECTOR INTELLIGENCE REPORT
Targets: {', '.join(self.TARGET_ENTITIES[:6])}...

{intel}

Key Question: Is Eskom or any water utility procuring technology, 
consulting, or AI services in the next 90 days?
""".strip()


# ─────────────────────────────────────────────
# 3. GOVERNMENT AGENT
# ─────────────────────────────────────────────

class GovernmentAgent(SectorAgent):
    name = "Government"

    TARGET_DEPARTMENTS = [
        "SITA (State Information Technology Agency)",
        "DPSA (Dept of Public Service and Administration)",
        "DTIC (Dept of Trade, Industry and Competition)",
        "National Treasury",
        "CSIR (Council for Scientific and Industrial Research)",
        "DTPS (Communications and Digital Technologies)",
        "South African Police Service (SAPS)",
        "Department of Home Affairs"
    ]

    # eTenders RSS / public procurement feeds
    SOURCES = [
        "https://www.etenders.gov.za/rss/latest_tenders",
        "https://www.sita.co.za/procurement/tenders",
    ]

    TENDER_KEYWORDS = [
        "artificial intelligence", "machine learning", "data analytics",
        "digital transformation", "ICT", "software", "technology",
        "automation", "system", "platform", "cloud", "consulting"
    ]

    def collect(self) -> str:
        all_text = []

        # Try eTenders RSS
        for url in self.SOURCES:
            items = self._fetch_rss(url, max_items=15)
            for item in items:
                combined = (item["title"] + " " + item["summary"]).lower()
                if any(kw in combined for kw in self.TENDER_KEYWORDS):
                    all_text.append(
                        f"TENDER: {item['title']}\n"
                        f"LINK: {item['link']}\n"
                        f"DETAIL: {item['summary']}"
                    )

        raw = "\n\n".join(all_text) if all_text else (
            "No matching tenders from RSS. Manual check of etenders.gov.za recommended."
        )
        intel = self._extract_intelligence(raw, "government procurement and digital transformation")

        return f"""
GOVERNMENT SECTOR INTELLIGENCE REPORT
Monitoring: {', '.join(self.TARGET_DEPARTMENTS[:5])}...

{intel}

Priority: Any AI, ICT, or digital transformation tender 
where Kgotla AI can submit a competitive proposal.
""".strip()


# ─────────────────────────────────────────────
# 4. ENTERPRISE AGENT
# ─────────────────────────────────────────────

class EnterpriseAgent(SectorAgent):
    name = "Enterprise"

    TARGET_CORPORATES = [
        "Sasol", "Anglo American", "Sibanye-Stillwater",
        "Murray & Roberts", "WBHO", "Aveng",
        "Transnet", "Airports Company South Africa (ACSA)",
        "South African Airways (SAA)", "Telkom SA",
        "Standard Bank", "Nedbank", "Absa", "FirstRand"
    ]

    SOURCES = [
        "https://www.businesslive.co.za/rss/",
        "https://www.moneyweb.co.za/feed/",
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=JSE&region=ZA&lang=en-ZA",
    ]

    def collect(self) -> str:
        all_text = []
        target_lower = [c.lower().split()[0] for c in self.TARGET_CORPORATES]

        for url in self.SOURCES:
            items = self._fetch_rss(url, max_items=12)
            for item in items:
                combined = (item["title"] + " " + item["summary"]).lower()
                if any(corp in combined for corp in target_lower) or \
                   any(kw in combined for kw in ["technology", "digital", "ai", "automation", "contract"]):
                    all_text.append(f"HEADLINE: {item['title']}\nSUMMARY: {item['summary']}")

        raw = "\n\n".join(all_text) if all_text else "No relevant corporate news retrieved."
        intel = self._extract_intelligence(raw, "large South African enterprise technology procurement")

        return f"""
ENTERPRISE SECTOR INTELLIGENCE REPORT
Tracking: {', '.join(self.TARGET_CORPORATES[:6])}...

{intel}

Key Question: Which JSE-listed or SOE entity is announcing 
a digital transformation, AI pilot, or technology spend this week?
""".strip()
