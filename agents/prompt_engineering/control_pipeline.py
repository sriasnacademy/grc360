import json
from groq import Groq
from connectors.lambda_mysql import call_lambda
from services.rag_service import save_process_to_rag
from config.servicekeys import GROQ_API_KEY
from services.main_bedrock_service import validate_with_guardrail
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_GROQ_LLAMA_8B, ACTOR_BEDROCK_GUARDRAIL,
)

client = Groq(api_key=GROQ_API_KEY)


def fetch_control_template(intent):
    payload = {"action": "select", "table": "prompt_templates", "where": {"template_name": intent}}
    result = call_lambda(payload)
    return result["records"][0]["content"] if result["count"] > 0 else None


def normalize_control_data(data: dict):
    if not data:
        return
    for key in ["control_name", "description", "control_type", "control_category"]:
        if key in data and isinstance(data[key], str):
            data[key] = " ".join(data[key].split()).strip()
    if "control_type" in data and data["control_type"]:
        data["control_type"] = data["control_type"].capitalize()
    if "control_category" in data and data["control_category"]:
        data["control_category"] = data["control_category"].capitalize()
    return data


def insert_control(data):
    payload = {
        "action": "insert",
        "table":  "control",
        "data": {
            "control_name":     data.get("control_name", ""),
            "description":      data.get("description", ""),
            "control_type":     data.get("control_type", ""),
            "control_category": data.get("control_category", ""),
        }
    }
    result = call_lambda(payload)
    return result.get("inserted_id")


def safe_json_parse(text: str):
    if not text or not text.strip():
        return None
    text = text.strip().replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end   = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception as e:
        print("JSON PARSE ERROR:", e)
        return None


def _extract_guardrail_reason(details: dict) -> str:
    reason = details.get("actionReason")
    if reason:
        return reason
    for key in ["topicPolicy", "contentPolicy", "wordPolicy", "sensitiveInformationPolicy"]:
        assessments = details.get("assessments", [])
        if isinstance(assessments, list) and assessments and key in assessments[0]:
            return f"{key} triggered"
    return "unsafe_or_unusual_content_detected"


def _run_guardrail_check(text: str, source: str, stage: str):
    try:
        result = validate_with_guardrail(text, source=source)
    except Exception as e:
        return {"allowed": False, "message": f"Safety check failed at {stage}: {str(e)}", "result": None}

    print(f"Guardrail [{stage}] action:", result.get("action"))
    if not result.get("is_valid", False):
        details = (result or {}).get("details", {}) or {}
        reason  = _extract_guardrail_reason(details)
        msg     = f"Request blocked at {stage}. Reason: {reason}."
        return {"allowed": False, "message": msg, "result": result}

    return {"allowed": True, "message": "passed", "result": result}


def run_control_pipeline(intent, raw_text):
    try:
        template = fetch_control_template(intent)
        if not template:
            return "Control template missing"

        # ── 1. Guardrail check on input ──────────────────────────────
        input_check = _run_guardrail_check(raw_text, source="INPUT", stage="input text")

        attribution_agent.record(
            action_type      = ActionType.GUARDRAIL_CHECK,
            actor            = ACTOR_BEDROCK_GUARDRAIL,
            sources          = [Source("ctrl-input", "User Input", "text", "user_prompt", excerpt=raw_text[:200])],
            decision_summary = f"Input guardrail: {'PASSED' if input_check['allowed'] else 'BLOCKED'}",
            reasoning        = input_check["message"],
            confidence       = ConfidenceLevel.HIGH,
            tags             = ["guardrail", "control-pipeline", "input"],
        )

        if not input_check["allowed"]:
            return input_check["message"]

        prompt = f"""
{template}

### Raw Text:
{raw_text}

### Rules:
Return ONLY valid JSON.
No explanation.
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw_output = response.choices[0].message.content
        print("RAW Control RESPONSE:", repr(raw_output))

        parsed_data = safe_json_parse(raw_output)
        if not parsed_data:
            return "Invalid JSON returned by LLM"

        cleaned_data = normalize_control_data(parsed_data)
        if not cleaned_data:
            return "Control data normalization failed"

        cid = insert_control(cleaned_data)
        save_process_to_rag("CONTROL", cleaned_data, cid)

        # ── 2. Attribution record for pipeline ──────────────────────
        attribution_agent.record(
            action_type      = ActionType.CONTROL_PIPELINE,
            actor            = ACTOR_GROQ_LLAMA_8B,
            sources          = [
                Source("ctrl-input",    "User Input",        "text",     "user_prompt",    excerpt=raw_text[:200]),
                Source("ctrl-template", "Prompt Template",   "database", f"prompt_templates[{intent}]"),
                Source("ctrl-output",   "LLM Response",      "llm",      "groq/llama-3.1-8b", excerpt=raw_output[:200]),
            ],
            decision_summary = (
                f"Control '{cleaned_data.get('control_name', '')}' inserted with ID {cid}. "
                f"Type: {cleaned_data.get('control_type')}, Category: {cleaned_data.get('control_category')}"
            ),
            reasoning        = (
                f"User described a control in free text. LLaMA 3.1-8B extracted structured fields "
                f"using template '{intent}'. Data normalised and saved to DB + RAG."
            ),
            confidence       = ConfidenceLevel.HIGH,
            tags             = ["control", "pipeline", intent.lower()],
        )
        # ─────────────────────────────────────────────────────────────

        return "Control inserted successfully"

    except Exception as e:
        return f"Control Pipeline Error: {str(e)}"
