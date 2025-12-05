import json
from agents.prompt_engineering.system_prompts import GetCategoryfromIntentAgent   # adjust import path

class IntentAgent:

    def __init__(self, llm_client):
        self.llm = llm_client

    def classify_intent(self, user_message: str):
        prompt = f"""
You are an Intent Classification Agent for the GRC360 application.

Given the following user message:
"{user_message}"

Identify the correct intent from this list:
- CREATE_PROCESS
- UPDATE_PROCESS
- DELETE_PROCESS
- QUERY_PROCESS
- CREATE_CONTROL
- UPDATE_CONTROL
- OTHER

Respond ONLY in this JSON format:
{{
  "intent": "<one of the above intents>",
  "confidence": "<percentage from 0 to 100>"
}}
"""

        # ✅ Call LLM
        response = self.llm.generate(prompt)

        # ✅ Parse Intent safely
        try:
            parsed = json.loads(response)
            intent = parsed.get("intent", "OTHER")
        except:
            intent = "OTHER"

        # ✅ Call Category Handler right here
        GetCategoryfromIntentAgent(intent, user_message)

        # ✅ Return intent only
        return intent
