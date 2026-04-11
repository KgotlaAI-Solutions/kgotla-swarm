"""
Kgotla AI Intelligence Swarm — Sector Agents
Mining / Energy / Government / Enterprise
POPIA NOTE: Only public data collected. No personal information stored.
"""

import re
import requests
import xml.etree.ElementTree as ET
from model_router import router, TaskType


class SectorAgent:
    def collect(self) -> str:
        raise NotImplementedError

    def _fetch_rss(self, url: str, max_items: int = 10) -> list:
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
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "KgotlaAI/1.0 (+https://kgotlaai.co.za)"})
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:max_chars]
        except Exception as e:
            return f"Page fetch failed: {e}"

    def _extract_intelligence(self, raw_text: str, focus: str) -> str:
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

Respond in plain text with 3-5 bullet points. Be specific — include company names,
rand values, and deadlines where visible. Always use today's actual date context.
"""
        response = router.route(prompt=prompt, task_type=TaskType.EXTRACTION, max_tokens=800)
        return response.content if response.success else f"Extraction failed: {response.error}"


class MiningAgent(SectorAgent):
    TARGET_ENTITIES = [
        "Sibanye-Stillwater", "Anglo American Platinum", "Impala Platinum",
        "Northam Platinum", "Harmony Gold", "Gold Fields", "AngloGold Ashanti",
        "Palabora Mining", "Kumba Iron Ore", "Exxaro Resources",
        "DMRE", "Council for Geoscience"
    ]
    SOURCES = [
        "https://www.miningmx.com/feed/",
        "https://www.engineeringnews.co.za/rss/mining.rss",
    ]

    def collect(self) -> str:
        all_text = []
        for url in self.SOURCES:
            for item in self._fetch_rss(url, max_items=8):
                all_text.append(f"HEADLINE: {item['title']}\nSUMMARY: {item['summary']}")
        raw   = "\n\n".join(all_text) or "No mining news retrieved."
        intel = self._extract_intelligence(raw, "mining")
        return f"MINING SECTOR INTELLIGENCE\nTargets: {', '.join(self.TARGET_ENTITIES[:6])}\n\n{intel}"


class EnergyAgent(SectorAgent):
    TARGET_ENTITIES = [
        "Eskom", "Rand Water", "Umgeni Water", "Lepelle Northern Water",
        "NERSA", "DWS", "IPP Office", "SANEDI", "City Power", "Tshwane Metro"
    ]
    SOURCES = [
        "https://www.engineeringnews.co.za/rss/energy.rss",
        "https://www.dailymaverick.co.za/rss/",
    ]

    def collect(self) -> str:
        all_text = []
        for url in self.SOURCES:
            for item in self._fetch_rss(url, max_items=8):
                if any(kw in item["title"].lower() for kw in
                       ["eskom","energy","power","water","nersa","solar","load","grid"]):
                    all_text.append(f"HEADLINE: {item['title']}\nSUMMARY: {item['summary']}")
        nersa_text = self._fetch_page_text("https://www.nersa.org.za/applications/", max_chars=4000)
        all_text.append(f"NERSA PORTAL: {nersa_text}")
        raw   = "\n\n".join(all_text) or "No energy news retrieved."
        intel = self._extract_intelligence(raw, "energy and water utilities")
        return f"ENERGY & WATER SECTOR INTELLIGENCE\nTargets: {', '.join(self.TARGET_ENTITIES[:6])}\n\n{intel}"


class GovernmentAgent(SectorAgent):
    TARGET_DEPARTMENTS = [
        "SITA", "DPSA", "DTIC", "National Treasury",
        "CSIR", "DTPS", "SAPS", "Home Affairs"
    ]
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
        for url in self.SOURCES:
            for item in self._fetch_rss(url, max_items=15):
                combined = (item["title"] + " " + item["summary"]).lower()
                if any(kw in combined for kw in self.TENDER_KEYWORDS):
                    all_text.append(
                        f"TENDER: {item['title']}\nLINK: {item['link']}\nDETAIL: {item['summary']}"
                    )
        raw   = "\n\n".join(all_text) or "No matching tenders. Manual check of etenders.gov.za recommended."
        intel = self._extract_intelligence(raw, "government procurement and digital transformation")
        return f"GOVERNMENT SECTOR INTELLIGENCE\nMonitoring: {', '.join(self.TARGET_DEPARTMENTS[:5])}\n\n{intel}"


class EnterpriseAgent(SectorAgent):
    TARGET_CORPORATES = [
        "Sasol", "Anglo American", "Sibanye-Stillwater", "Murray & Roberts",
        "Transnet", "ACSA", "Telkom SA", "Standard Bank", "Nedbank", "Absa"
    ]
    SOURCES = [
        "https://www.businesslive.co.za/rss/",
        "https://www.moneyweb.co.za/feed/",
    ]

    def collect(self) -> str:
        all_text  = []
        corp_keys = [c.lower().split()[0] for c in self.TARGET_CORPORATES]
        for url in self.SOURCES:
            for item in self._fetch_rss(url, max_items=12):
                combined = (item["title"] + " " + item["summary"]).lower()
                if any(c in combined for c in corp_keys) or \
                   any(kw in combined for kw in ["technology","digital","ai","automation","contract"]):
                    all_text.append(f"HEADLINE: {item['title']}\nSUMMARY: {item['summary']}")
        raw   = "\n\n".join(all_text) or "No relevant corporate news retrieved."
        intel = self._extract_intelligence(raw, "large South African enterprise technology procurement")
        return f"ENTERPRISE SECTOR INTELLIGENCE\nTracking: {', '.join(self.TARGET_CORPORATES[:6])}\n\n{intel}"
