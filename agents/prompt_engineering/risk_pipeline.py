import json
import re
from groq import Groq
from connectors.lambda_mysql import call_lambda
from services.rag_service import save_process_to_rag
from config.servicekeys import GROQ_API_KEY
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_GROQ_LLAMA_70B,
)

client = Groq(api_key=GROQ_API_KEY)


def fetch_risk_template(intent):
    payload = {"action": "select", "table": "prompt_templates", "where": {"template_name": intent}}
    result = call_lambda(payload)
    return result["records"][0]["content"] if result.get("count", 0) > 0 else None


def safe_json_parse(text: str):
    if not text or not text.strip():
        return None
    text = text.strip().replace("```json", "").replace("```", "").strip()
    start = text.find("{"); end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception as e:
        print("❌ JSON PARSE ERROR:", e)
        return None


def normalize_risk_data(data: dict):
    if not data:
        return None
    for key in ["risk_name", "description", "cause", "impact", "likelihood", "mitigation", "status", "owner", "severity"]:
        if key in data and isinstance(data[key], str):
            data[key] = " ".join(data[key].split()).strip()
    data["status"] = data.get("status", "Active").capitalize()
    if "likelihood" in data:
        data["likelihood"] = data["likelihood"].capitalize()
    return data


def insert_risk(data):
    payload = {
        "action": "insert",
        "table":  "risk",
        "data": {
            "risk_name":   data.get("risk_name", ""),
            "description": data.get("description", ""),
            "cause":       data.get("cause", ""),
            "impact":      data.get("impact", ""),
            "likelihood":  data.get("likelihood", ""),
            "mitigation":  data.get("mitigation", ""),
            "status":      data.get("status", ""),
            "owner":       data.get("owner", ""),
            "severity":    data.get("severity", ""),
        }
    }
    result = call_lambda(payload)
    return result.get("inserted_id")


def run_risk_pipeline(intent, raw_text):
    try:
        template = fetch_risk_template(intent)
        if not template:
            return "❌ Risk template missing"

        prompt = f"""
{template}

### Raw Text:
{raw_text}

### Rules:
- Return ONLY valid JSON
- Do NOT wrap in ```json
- Do NOT use arrays or lists
- All values must be strings
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw_output = response.choices[0].message.content
        print("🔍 RAW RISK RESPONSE:", repr(raw_output))

        parsed_data = safe_json_parse(raw_output)
        if not parsed_data:
            return "❌ Invalid JSON returned by LLM"

        cleaned_data = normalize_risk_data(parsed_data)
        if not cleaned_data:
            return "❌ RISK data normalization failed"

        risk_id = insert_risk(cleaned_data)
        save_process_to_rag("RISK", cleaned_data, risk_id)

        # ── Attribution record ───────────────────────────────────────
        attribution_agent.record(
            action_type      = ActionType.RISK_PIPELINE,
            actor            = ACTOR_GROQ_LLAMA_70B,
            sources          = [
                Source("risk-input",    "User Input",      "text",     "user_prompt",           excerpt=raw_text[:200]),
                Source("risk-template", "Prompt Template", "database", f"prompt_templates[{intent}]"),
                Source("risk-output",   "LLM Response",    "llm",      "groq/llama-3.3-70b",   excerpt=raw_output[:200]),
            ],
            decision_summary = (
                f"Risk '{cleaned_data.get('risk_name', '')}' inserted with ID {risk_id}. "
                f"Severity: {cleaned_data.get('severity')}, Likelihood: {cleaned_data.get('likelihood')}"
            ),
            reasoning        = (
                f"Free-text risk description processed via LLaMA 3.3-70B using template '{intent}'. "
                f"Fields extracted: name, description, cause, impact, likelihood, mitigation, owner, severity."
            ),
            confidence       = ConfidenceLevel.HIGH,
            tags             = ["risk", "pipeline", cleaned_data.get("severity", "").lower()],
        )
        # ────────────────────────────────────────────────────────────

        return "✅ RISK inserted successfully"

    except Exception as e:
        return f"❌ RISK Pipeline Error: {str(e)}"
