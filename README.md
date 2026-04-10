# Kgotla AI Intelligence Swarm

Multi-agent AI system that delivers daily sector intelligence
for South Africa's mining, energy, government, and enterprise markets.

## Files

```
kgotla_swarm/
├── main.py              ← Entry point. Run this.
├── governor_agent.py    ← Orchestrator. Synthesises all reports.
├── sector_agents.py     ← Mining / Energy / Government / Enterprise agents.
├── model_router.py      ← Routes tasks to correct free AI model.
├── requirements.txt     ← Python dependencies.
└── briefs/              ← Auto-created. Stores daily JSON briefs.
    └── latest.json      ← Always the most recent brief.
```

## Quick Start (Local)

```bash
cd kgotla_swarm
pip install -r requirements.txt

# Create .env file with your free API keys:
# GROQ_API_KEY=your_groq_key_here
# GOOGLE_AI_API_KEY=your_google_ai_key_here
# HF_API_TOKEN=your_huggingface_token_here

python main.py
```

## Free API Keys — Where To Get Them

| Key | URL | Free Tier |
|-----|-----|-----------|
| GROQ_API_KEY | https://console.groq.com/keys | 14,400 req/day free |
| GOOGLE_AI_API_KEY | https://aistudio.google.com/app/apikey | 1,500 req/day free |
| HF_API_TOKEN | https://huggingface.co/settings/tokens | Unlimited inference |

## Deploy on Railway (Free)

1. Push this folder to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Set environment variables (GROQ_API_KEY etc.) in Railway dashboard
4. Set Start Command: `python main.py`
5. Add a Cron Job in Railway: `0 4 * * *` (runs at 06:00 SAST = 04:00 UTC)

## Architecture

```
Governor Agent (LLaMA 3.3 70B via Groq)
    │
    ├── Mining Agent      → Mining news RSS → extraction → report
    ├── Energy Agent      → Eskom/NERSA/water RSS → report
    ├── Government Agent  → eTenders portal → tender matching → report
    └── Enterprise Agent  → JSE/business news → deal signals → report

All agents feed into → Model Router → picks best free model per task
```

## Legal Notes (South Africa)

- Only public data is collected (eTenders, public RSS, NERSA public notices)
- POPIA compliant: no personal information is stored
- robots.txt is respected; rate limiting is built in (1 cycle per day)
- Model licenses: LLaMA 3.3 (Meta Community License), Mistral (Apache 2.0),
  IBM Granite (Apache 2.0), Gemini (Google AI Studio Terms of Service)
- All free tier usage. No resale of API access.

---
Built by Kgotla AI Consulting PTY Ltd — kgotlaai.co.za
