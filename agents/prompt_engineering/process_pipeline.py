from groq import Groq
from connectors.lambda_mysql import call_lambda
import json
from services.rag_service import save_process_to_rag
from config.servicekeys import GROQ_API_KEY
from services.rag_retrieval_service import (
    extract_process_ids_from_rag_for_duplicate_check,
    rag_find_process_ids
)
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

    result = call_lambda(payload)

    process_id = result.get("inserted_id")
    if not process_id:
        raise RuntimeError("MySQL insert failed – no process_id returned")

    return process_id


# ----------------------------
# Main pipeline function
# ----------------------------
def run_process_pipeline(intent, raw_text):
    try:
        print("📤 Intent received:", intent)

        # ===============================
        # STEP 0: RAG DUPLICATE CHECK
        # ===============================

        rag_results = rag_find_process_ids(
            query=raw_text,
            entitytype="PROCESS",
            top_k=3
        )

        duplicate_process_ids = extract_process_ids_from_rag_for_duplicate_check(
            rag_results,
            min_similarity=0.7
        )

        # 🚫 DUPLICATE FOUND → STOP
        if duplicate_process_ids:
            print("🚫 Duplicate process IDs found:", duplicate_process_ids)
            return "❌ Process already exists. Duplicate detected in RAG."

        # ===============================
        # ELSE → CONTINUE PIPELINE
        # ===============================

        template = fetch_prompt_template(intent)
        if not template:
            return "❌ Prompt template not found."

        final_prompt = f"""
{template}

### Raw Text:
{raw_text}

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
