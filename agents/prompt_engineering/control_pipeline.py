import json
from groq import Groq
from connectors.lambda_mysql import call_lambda
from services.rag_service import save_process_to_rag

client = Groq(api_key="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")


def fetch_control_template(intent):
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
def normalize_control_data(data: dict):
    if not data:
        return None

    # Clean and strip string fields
    for key in ["control_name", "description", "control_type", "control_category"]:
        if key in data and isinstance(data[key], str):
            data[key] = " ".join(data[key].split()).strip()

    # Capitalize type and category for consistency
    if "control_type" in data and data["control_type"]:
        data["control_type"] = data["control_type"].capitalize()
    if "control_category" in data and data["control_category"]:
        data["control_category"] = data["control_category"].capitalize()

    return data

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
    control_id = call_lambda(payload)
    return control_id

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
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw_output = response.choices[0].message.content
        print("🔍 RAW Control RESPONSE:", repr(raw_output))

        parsed_data = safe_json_parse(raw_output)
        if not parsed_data:
            return "❌ Invalid JSON returned by LLM"

        cleaned_data = normalize_control_data(parsed_data)
        if not cleaned_data:
            return "❌ Control data normalization failed"

        cid = insert_control(cleaned_data)
        
        #RAG INSERTION
        save_process_to_rag("CONTROL",cleaned_data,cid)


        return "✅ Control inserted successfully"

    except Exception as e:
        return f"❌ Control Pipeline Error: {str(e)}"
