import json
from groq import Groq
from connectors.lambda_mysql import call_lambda

client = Groq(api_key="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")


def fetch_control_template(intent):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"template_name": intent}
    }
    result = call_lambda(payload)
    return result["records"][0]["content"] if result["count"] > 0 else None


def insert_control(data):
    payload = {
        "action": "insert",
        "table": "control",
        "data": {
            "control_name": data.get("control_name", ""),
            "description": data.get("description", ""),
            "control_type": data.get("control_type", ""),
            "control_category": data.get("control_category", "")
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


def run_control_pipeline(intent, raw_text):
    try:
        template = fetch_control_template(intent)
        if not template:
            return "❌ control template missing"

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
        print("🔍 RAW CONTROL RESPONSE:", repr(raw_output))

        data = safe_json_parse(raw_output)

        if not data:
            return "❌ Invalid JSON returned by LLM"

        insert_control(data)

        return "✅ Control inserted successfully"

    except Exception as e:
        return f"❌ Control Pipeline Error: {str(e)}"

