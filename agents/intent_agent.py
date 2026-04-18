import json
from models.my_llm_client import LLMClient
from connectors.lambda_mysql import call_lambda
from agents.prompt_engineering.system_prompts import route_pipeline
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_GROQ_LLAMA_70B,
)


class IntentAgent:

    def __init__(self):
        self.llm = LLMClient()

    @staticmethod
    def fetch_prompt_template(category="INTENT_CLASSIFICATION"):
        payload = {
            "action": "select",
            "table":  "prompt_templates",
            "where":  {"category": category}
        }
        data = call_lambda(payload)
        if data.get("count", 0) == 0:
            return None
        return data["records"][0]["content"]

    def classify_intent(self, raw_text):
        try:
            template = self.fetch_prompt_template("INTENT_CLASSIFICATION")
            if not template:
                return "OTHER", "❌ INTENT template missing in DB"

            prompt = f"""
{template}

### Input:
{raw_text}

### Available Intents (Choose ONLY one):
- CREATE_PROCESS, CREATE_RISK, CREATE_CONTROL, CREATE_SUBPROCESS, CREATE_TEST_PLAN
- QUERY_PROCESS, QUERY_RISK, QUERY_CONTROL, QUERY_SUBPROCESS, QUERY_TEST_PLAN
- REPORT_STATISTICAL, REPORT_CONFIDENCE, REPORT_AUDIT_TRAIL, REPORT_ENHANCED, REPORT_GENERAL
- LINK_PROCESS_SUBPROCESS, LINK_PROCESS_RISK, LINK_RISK_CONTROL, LINK_TEST_PLAN_CONTROL etc.
- OTHER

### Rules:
- If the user asks for **statistics, confidence levels, audit trail, trends, summary, analytics, or report** → use one of the REPORT_* intents.
- Examples:
  - "show me confidence levels across pipelines" → REPORT_CONFIDENCE
  - "statistical report on controls" → REPORT_STATISTICAL
  - "enhanced audit trail" → REPORT_AUDIT_TRAIL
  - "summary of all AI decisions" → REPORT_GENERAL
- For simple "show me processes" or "view risks" → use QUERY_*
- Return STRICT JSON only. No markdown.

Format:
{{
  "intent": "REPORT_CONFIDENCE",
  "confidence": 85
}}
"""

            response = self.llm.generate(prompt)
            print("🔍 RAW INTENT AI:", repr(response))

            intent = "OTHER"
            if response:
                clean = response.replace("```json", "").replace("```", "").strip()
                try:
                    parsed = json.loads(clean)
                    intent = parsed.get("intent", "OTHER")
                except Exception:
                    pass

            print("✅ INTENT:", intent)

            # ── Attribution record ──────────────────────────────────────
            attribution_agent.record(
                action_type      = ActionType.INTENT_CLASSIFICATION,
                actor            = ACTOR_GROQ_LLAMA_70B,
                sources          = [
                    Source("intent-input", "User Input", "text", "user_prompt",
                           excerpt=raw_text[:200]),
                    Source("intent-template", "Prompt Template DB",
                           "database", "prompt_templates[INTENT_CLASSIFICATION]"),
                ],
                decision_summary = f"Intent classified as: {intent}",
                reasoning        = (
                    f"LLM parsed user input against INTENT_CLASSIFICATION template. "
                    f"Raw output: {repr(response)[:200]}"
                ),
                confidence       = ConfidenceLevel.HIGH if intent != "OTHER" else ConfidenceLevel.LOW,
                tags             = ["intent", intent.lower()],
            )
            # ───────────────────────────────────────────────────────────

            result = route_pipeline(intent, raw_text)
            return intent, result or "⚠ No response from pipeline"

        except Exception as e:
            print("❌ INTENT AGENT ERROR:", str(e))
            return "OTHER", f"❌ IntentAgent crash: {e}"
