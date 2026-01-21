import json
import re
from groq import Groq
from connectors.lambda_mysql import call_lambda
from services.rag_service import save_process_to_rag
from config.servicekeys import GROQ_API_KEY

# -----------------------------------------
# GROQ CLIENT
# -----------------------------------------
client = Groq(api_key=GROQ_API_KEY)


# -----------------------------------------
# FETCH SUBPROCESS PROMPT TEMPLATE
# -----------------------------------------
def fetch_sub_porcess_template(intent):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"template_name": intent}
    }
    result = call_lambda(payload)
    
    return result


# -----------------------------------------
# SAFE JSON PARSER (KEEP AS IS – GOOD)
# -----------------------------------------
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
        return json.loads(text[start:end + 1])
    except Exception as e:
        print("❌ JSON PARSE ERROR:", e)
        print("❌ RAW TEXT:", repr(text))
        return None


# -----------------------------------------
# NORMALIZE SUBPROCESS DATA (🔥 KEY FIX)
# -----------------------------------------
def normalize_subprocess_data(data: dict):
    if not data:
        return None

    # Convert outcomes list → string
    if isinstance(data.get("outcomes"), list):
        data["outcomes"] = ", ".join(data["outcomes"])

    # Remove line breaks & extra spaces
    if "description" in data:
        data["description"] = " ".join(data["description"].split())

    # Normalize case
    data["frequency"] = data.get("frequency", "").capitalize()
    data["status"] = data.get("status", "Active").capitalize()

    return data


# -----------------------------------------
# INSERT SUBPROCESS
# -----------------------------------------
def insert_subprocess(data):
    payload = {
        "action": "insert",
        "table": "sub_processes",
        "data": {
            "sub_process_name": data.get("sub_process_name", ""),
            "description": data.get("description", ""),
            "department": data.get("department", ""),
            "sub_process_owner": data.get("sub_process_owner", ""),
            "frequency": data.get("frequency", ""),
            "triggers": data.get("triggers", ""),
            "outcomes": data.get("outcomes", ""),
            "status": data.get("status", "Active"),
        }
    }

    result = call_lambda(payload)
    subprocessid = result.get("inserted_id")
    
    return subprocessid


# -----------------------------------------
# MAIN SUBPROCESS PIPELINE
# -----------------------------------------
def run_subporcess_pipeline(intent, raw_text):
    try:
        template = fetch_sub_porcess_template(intent)
        if not template:
            return "❌ Subprocess template missing"

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
            temperature=0
        )

        raw_output = response.choices[0].message.content
        print("🔍 RAW SUBPROCESS RESPONSE:", repr(raw_output))

        parsed_data = safe_json_parse(raw_output)
        if not parsed_data:
            return "❌ Invalid JSON returned by LLM"

        cleaned_data = normalize_subprocess_data(parsed_data)
        if not cleaned_data:
            return "❌ Subprocess data normalization failed"

        subprocessid = insert_subprocess(cleaned_data)
        
        save_process_to_rag("SUB_PROCESS", cleaned_data, subprocessid)

        return "✅ Subprocess inserted successfully"

    except Exception as e:
        return f"❌ Subprocess Pipeline Error: {str(e)}"
