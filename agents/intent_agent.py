import json
from models.my_llm_client import LLMClient
from connectors.lambda_mysql import call_lambda
from agents.prompt_engineering.system_prompts import route_pipeline


class IntentAgent:

    def __init__(self):
        self.llm = LLMClient()


    # ----------------------------------------------
    # FETCH INTENT PROMPT TEMPLATE FROM LAMBDA
    # ----------------------------------------------
    @staticmethod
    def fetch_prompt_template(category="INTENT_CLASSIFICATION"):

        payload = {
            "action": "select",
            "table": "prompt_templates",
            "where": { "category": category }
        }

        data = call_lambda(payload)

        if data.get("count", 0) == 0:
            return None

        return data["records"][0]["content"]


    # ----------------------------------------------
    # DETECT INTENT
    # ----------------------------------------------
    def classify_intent(self, raw_text):

        try:
            template = self.fetch_prompt_template("INTENT_CLASSIFICATION")

            if not template:
                return "OTHER", "❌ INTENT template missing in DB"

            # ✅ PROMPT
            prompt = f"""
{template}

### Input:
{raw_text}

### Rules:
Return STRICT JSON only.
No markdown.
Format:
{{ "intent": "VALUE" }}
"""

            response = self.llm.generate(prompt)

            print("🔍 RAW INTENT AI:", repr(response))

            intent = "OTHER"

            if response:
                clean = response.replace("```json","").replace("```","").strip()
                try:
                    parsed = json.loads(clean)
                    intent = parsed.get("intent", "OTHER")
                except:
                    pass

            print("✅ INTENT:", intent)

            # ✅ RUN CORE PIPELINE
            result = route_pipeline(intent, raw_text)
            return intent, result or "⚠ No response from pipeline"

        except Exception as e:
            print("❌ INTENT AGENT ERROR:", str(e))
            return "OTHER", f"❌ IntentAgent crash: {e}"