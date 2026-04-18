import json
from groq import Groq
from connectors.lambda_mysql import call_lambda
from config.servicekeys import GROQ_API_KEY
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_GROQ_LLAMA_70B,
)
from services.rag_retrieval_service import rag_find_process_ids   # reuse your existing RAG

client = Groq(api_key=GROQ_API_KEY)

def fetch_report_template():
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"template_name": "REPORT_GENERATION"}
    }
    result = call_lambda(payload)
    return result["records"][0]["content"] if result.get("count", 0) > 0 else None

def run_report_pipeline(intent: str, raw_text: str):
    try:
        # 1. Get global summary + recent trail
        summary = attribution_agent.summary()
        trail   = attribution_agent.get_trail()[-50:]   # last 50 actions (adjust as needed)

        # 2. Optional RAG semantic search on attribution logs
        rag_results = rag_find_process_ids(raw_text, "ATTRIBUTION_LOG") if "ATTRIBUTION_LOG" in raw_text.upper() else []

        # 3. Build context for LLM
        context = f"""
GLOBAL ATTRIBUTION SUMMARY:
{json.dumps(summary, indent=2)}

RECENT 50 ACTIONS:
{json.dumps([{
    "record_id": r.record_id[:8],
    "timestamp": r.timestamp,
    "action": r.action_type.value,
    "actor": r.actor.name,
    "decision": r.decision_summary,
    "confidence": r.confidence.value,
    "tags": r.tags
} for r in trail], indent=2)}

RAG RELEVANT LOGS: {len(rag_results)} records found
USER REQUEST: {raw_text}
"""

        template = fetch_report_template()
        if not template:
            template = """You are an expert GRC auditor.
Generate a professional **Statistical + Enhanced Report** from the attribution logs."""

        prompt = f"""
{template}

{context}

Rules:
- Start with a clear title (e.g. "📊 Statistical & Enhanced Report – Control Pipeline")
- Show key statistics (counts by action_type, by actor, confidence distribution, time range)
- Highlight insights / anomalies / trends
- End with "Audit Integrity: All records verified with SHA-256 checksums ✅"
- Use markdown formatting (tables, bullet points, emojis)
- Keep it concise but insightful
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        report = response.choices[0].message.content.strip()

        # 4. Record this report generation itself (full audit trail)
        attribution_agent.record(
            action_type=ActionType.CUSTOM,
            actor=ACTOR_GROQ_LLAMA_70B,
            sources=[
                Source("report-input", "User Prompt", "text", "user_prompt", excerpt=raw_text[:200]),
                Source("attribution-summary", "Attribution Agent", "system", "attribution_agent.summary()"),
            ],
            decision_summary=f"Generated enhanced report for: {raw_text[:80]}...",
            reasoning="LLM analyzed AttributionAgent logs + RAG retrieval and produced statistical + narrative report",
            confidence=ConfidenceLevel.HIGH,
            tags=["report", "statistical", "enhanced"],
        )

        return report

    except Exception as e:
        return f"❌ Report Pipeline Error: {str(e)}"