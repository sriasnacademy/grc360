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
def fetch_risk_template(intent):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"template_name": intent}
    }
    result = call_lambda(payload)
    return result["records"][0]["content"] if result.get("count", 0) > 0 else None

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
def normalize_risk_data(data: dict):
    if not data:
        return None

    # Ensure all string fields are stripped and cleaned
    for key in ["risk_name", "description", "cause", "impact", "likelihood", "mitigation", "status", "owner", "severity"]:
        if key in data and isinstance(data[key], str):
            # Remove extra spaces and line breaks
            data[key] = " ".join(data[key].split()).strip()

    # Capitalize status
    data["status"] = data.get("status", "Active").capitalize()

    # Optionally capitalize likelihood if you want consistency
    if "likelihood" in data:
        data["likelihood"] = data["likelihood"].capitalize()

    return data # -----------------------------------------
# INSERT RISK
# -----------------------------------------
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

    result = call_lambda(payload)

    risk_id = result.get("inserted_id")
    
    return risk_id

# -----------------------------------------
# MAIN SUBPROCESS PIPELINE
# -----------------------------------------
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
            temperature=0
        )

        raw_output = response.choices[0].message.content
        print("🔍 RAW RISK RESPONSE:", repr(raw_output))

        parsed_data = safe_json_parse(raw_output)
        if not parsed_data:
            return "❌ Invalid JSON returned by LLM"

        cleaned_data = normalize_risk_data(parsed_data)
        if not cleaned_data:
            return "❌ RISK data normalization failed"

        riskid = insert_risk(cleaned_data)
        
        #RAG INSERTION
        save_process_to_rag("RISK",cleaned_data,riskid)

        return "✅ RISK inserted successfully"

    except Exception as e:
        return f"❌ RISK Pipeline Error: {str(e)}"


