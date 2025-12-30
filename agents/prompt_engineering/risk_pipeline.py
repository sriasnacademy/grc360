import json
from groq import Groq
from connectors.lambda_mysql import call_lambda

client = Groq(api_key="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")


def fetch_risk_template(intent):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"template_name": intent}
    }
    result = call_lambda(payload)
    return result["records"][0]["content"] if result["count"] > 0 else None


def insert_risk(data):
    payload = {
        "action": "insert",
        "table": "risk",
        "data": {
            "risk_name": data.get("risk_name", ""),
            "description": data.get("description", ""),
            "cause": data.get("cause", ""),
            "impact": data.get("impact", ""),
            "likelihood": data.get("likelihood", ""),
            "mitigation": data.get("mitigation", ""),
            "status": data.get("status", ""),
            "owner": data.get("owner", ""),
            "severity": data.get("severity", "")
        }
    }
    call_lambda(payload)
    
def safe_json_parse(text: str):
    if not text or not text.strip():
        return None

    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    try:
        return json.loads(text[start:end+1])
    except Exception as e:
        print("❌ JSON PARSE ERROR:", e)
        print("❌ RAW TEXT:", repr(text))
        return None


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
Return ONLY valid JSON.
No explanation.
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw_output = response.choices[0].message.content
        print("🔍 RAW RISK RESPONSE:", repr(raw_output))

        data = safe_json_parse(raw_output)

        if not data:
            return "❌ Invalid JSON returned by LLM"

        insert_risk(data)

        return "✅ Risk inserted successfully"

    except Exception as e:
        return f"❌ Risk Pipeline Error: {str(e)}"

