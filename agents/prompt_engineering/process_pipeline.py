from groq import Groq
from connectors.lambda_mysql import call_lambda
import json
from services.rag_service import save_process_to_rag
from config.servicekeys import GROQ_API_KEY
from services.bedrock_check_all import check_content_with_guardrails

# ----------------------------
# Groq AI Client
# ----------------------------
client = Groq(api_key=GROQ_API_KEY)

# ----------------------------
# Fetch prompt template
# ----------------------------
def fetch_prompt_template(intent):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"template_name": intent}
    }
    result = call_lambda(payload)
    if result["count"] == 0:
        return None
    return result["records"][0]["content"]

# ----------------------------
# Insert into DB
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

    result = call_lambda(payload)
    process_id = result.get("inserted_id")

    if not process_id:
        raise RuntimeError("MySQL insert failed – no process_id returned")

    return process_id

# ----------------------------
# MAIN PIPELINE (UNCHANGED FLOW)
# ----------------------------
def run_process_pipeline(intent, raw_text):
    try:
        print("📤 Intent received:", intent)

        # ===============================
        # STEP 0: BEDROCK GUARDRAILS
        # ===============================
        guardrail_result = check_content_with_guardrails(raw_text)
        print(guardrail_result)
        if not guardrail_result["allowed"]:
            # 🔴 HARD STOP – USER SEES BLOCK MESSAGE
            return guardrail_result["message"]

        safe_text = guardrail_result["safe_text"] or raw_text
        print(safe_text)

        # ===============================
        # STEP 2: EXISTING LOGIC CONTINUES
        # ===============================
        template = fetch_prompt_template(intent)
        if not template:
            return "❌ Prompt template not found."

        final_prompt = f"""
{template}

### Raw Text:
{safe_text}

### Instructions:
Return ONLY valid JSON.
❌ Do NOT wrap in markdown.
✅ Output must start with {{ and end with }}.
"""

        response_ai = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
             messages=[{"role": "user", "content": final_prompt}],
            temperature=0.2
        )

        output = response_ai.choices[0].message.content.strip()
        clean = output.replace("```json", "").replace("```", "").strip()

        data = json.loads(clean)

        process_id = insert_into_table(data)
        save_process_to_rag("PROCESS", data, process_id)

        return "✅ Process Created Successfully."

    except json.JSONDecodeError:
        return "❌ AI returned invalid JSON."

    except RuntimeError as e:
        return str(e)

    except Exception as e:
        return f"❌ Pipeline Error: {str(e)}"
