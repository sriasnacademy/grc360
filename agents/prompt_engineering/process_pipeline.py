from groq import Groq
from connectors.lambda_mysql import call_lambda
import json
from services.rag_service import save_process_to_rag
from config.servicekeys import GROQ_API_KEY

# ----------------------------
# Groq AI Client
# ----------------------------
client = Groq(api_key=GROQ_API_KEY)

# ----------------------------
# Detect category using Lambda
# ----------------------------
def detect_category(intent, raw_text):
    # Direct mapping: intent = category
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"category": intent}
    }
    result = call_lambda(payload)
    if result["count"] > 0:
        return result["records"][0]["category"]

    # Fallback: keyword matching
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "columns": ["category"]
    }
    result = call_lambda(payload)
    raw_lower = raw_text.lower()
    for item in result["records"]:
        if item["category"].lower() in raw_lower:
            return item["category"]

    return result["records"][0]["category"] if result["records"] else None


# ----------------------------
# Fetch prompt template using Lambda
# ----------------------------
def fetch_prompt_template(category):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"category": category}
    }
    result = call_lambda(payload)
    if result["count"] == 0:
        return None
    return result["records"][0]["content"]
# -----------------------------------------
# NORMALIZE PROCESS DATA
# -----------------------------------------
def normalize_process_data(data: dict):
    if not data:
        return None

    # Clean and strip string fields
    for key in ["process_name", "description", "department", "owner", "frequency"]:
        if key in data and isinstance(data[key], str):
            data[key] = " ".join(data[key].split()).strip()

    # Capitalize frequency
    if "frequency" in data and isinstance(data["frequency"], str):
        data["frequency"] = data["frequency"].capitalize()

    # Convert triggers list → comma-separated string
    triggers = data.get("triggers")
    if isinstance(triggers, list):
        data["triggers"] = ", ".join(str(t).strip() for t in triggers)

    # Convert outcomes list → comma-separated string
    outcomes = data.get("outcomes")
    if isinstance(outcomes, list):
        data["outcomes"] = ", ".join(str(o).strip() for o in outcomes)

    return data

# ----------------------------
# Insert into DB using Lambda
# ----------------------------
def insert_into_table(data):
    payload = {
        "action": "insert",
        "table": "processes",
        "data": {
            "process_name": data.get("process_name", ""),
            "description": data.get("description", ""),
            "department": data.get("department", ""),
            "process_owner": data.get("owner", ""),
            "frequency": data.get("frequency", ""),
            "triggers": ",".join(data.get("triggers", [])),
            "outcomes": ",".join(data.get("outcomes", []))
        }
    }
    call_lambda(payload)
    return True


# ----------------------------
# Main pipeline function
# ----------------------------
def run_process_pipeline(intent, raw_text):
    try:
        print("📤 Intent received:", intent)

        # Step 1: Detect category
        category = detect_category(intent, raw_text)
        if not category:
            return "❌ No category mapping found."
        print("📂 Category:", category)

        # Step 2: Fetch prompt template
        template = fetch_prompt_template(category)
        if not template:
            return "❌ Prompt template not found."

        # Step 3: Build strong JSON prompt for Groq AI
        final_prompt = f"""
{template}

### Raw Text:
{raw_text}

### Instructions:
Return ONLY valid JSON.
❌ Do NOT wrap in markdown.
✅ Output must start with {{ and end with }}.
"""

        # Step 4: Call Groq AI
        response_ai = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.2
        )

        output = response_ai.choices[0].message.content.strip()
        clean = output.replace("```json", "").replace("```", "").strip()

        # Step 5: Parse AI JSON output
        data = json.loads(clean)

        # Step 6: Insert into DB via Lambda
        #insert_into_table(data)

        save_process_to_rag(data)

        return "✅ Process Created Successfully.."

    except json.JSONDecodeError:
        return "❌ AI returned invalid JSON."

    except RuntimeError as e:
        return str(e)

    except Exception as e:
        return f"❌ Pipeline Error: {str(e)}"
