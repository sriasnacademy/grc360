import json
from groq import Groq
from connectors.lambda_mysql import call_lambda
from services.rag_service import save_process_to_rag
from config.servicekeys import GROQ_API_KEY

# ----------------------------
# Groq AI Client
# ----------------------------
client = Groq(api_key=GROQ_API_KEY)

  
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
    result = call_lambda(payload)

    test_plan_id = result.get("inserted_id")
    if not test_plan_id:
        raise RuntimeError("MySQL insert failed – no test_plan_id returned")

    return test_plan_id
    
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
        print("📤 Intent received:", intent)

        # Step 1: Detect category

        # Step 2: Fetch prompt template
        template = fetch_test_plan_template(intent)
        if not template:
            return "❌ Test Plan prompt template not found."

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
        test_plan_id = insert_test_plan(data)

        # Step 7: Insert into PGVector / RAG
        save_process_to_rag("TEST_PLAN", data, test_plan_id)

        return "✅ Test Plan Created Successfully."

    except json.JSONDecodeError:
        return "❌ AI returned invalid JSON."

    except RuntimeError as e:
        return str(e)

    except Exception as e:
        return f"❌ Test Plan Pipeline Error: {str(e)}"
