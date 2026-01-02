import json
from groq import Groq
from connectors.lambda_mysql import call_lambda

client = Groq(api_key="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")


def fetch_test_plan_template(intent):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"template_name": intent}
    }
    result = call_lambda(payload)
    return result["records"][0]["content"] if result["count"] > 0 else None

# -----------------------------------------
# NORMALIZE CONTROL DATA
# -----------------------------------------
def normalize_test_plan_data(data: dict):
    if not data:
        return None

    # Clean and strip string fields
    for key in ["test_plan_name", "description", "module", "status"]:
        if key in data and isinstance(data[key], str):
            data[key] = " ".join(data[key].split()).strip()
    # Capitalize status
    data["status"] = data.get("status", "Active").capitalize()
    # Capitalize type and category for consistency
    if "test_plan_name" in data and data["test_plan_name"]:
        data["test_plan_name"] = data["test_plan_name"].capitalize()
    if "module" in data and data["module"]:
        data["module"] = data["module"].capitalize()

    return data

def insert_test_plan(data):
    payload = {
        "action": "insert",
        "table": "test_plan",
        "data": {
            "test_plan_name": data.get("test_plan_name", ""),
            "description": data.get("description", ""),
            "module": data.get("module", ""),
            "status": data.get("status", "Active")
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


def run_test_plan_pipeline(intent, raw_text):
    try:
        template = fetch_test_plan_template(intent)
        if not template:
            return "❌ Test Plan template missing"

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
        print("🔍 RAW Test Plan RESPONSE:", repr(raw_output))

        parsed_data = safe_json_parse(raw_output)
        if not parsed_data:
            return "❌ Invalid JSON returned by LLM"

        cleaned_data = normalize_test_plan_data(parsed_data)
        if not cleaned_data:
            return "❌ Test Plan data normalization failed"

        insert_test_plan(cleaned_data)

        return "✅ Test Plan inserted successfully"

    except Exception as e:
        return f"❌ Test Plan Pipeline Error: {str(e)}"
