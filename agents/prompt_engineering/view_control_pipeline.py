from connectors.lambda_mysql import call_lambda
from agents.prompt_engineering.common_name_extractor import extract_entity_name
from services.rag_retrieval_service import *


def run_view_control_pipeline(intent: str, raw_text: str):
    try:
        # Step 1️⃣ Semantic search (RAG)
        rag_results = rag_find_process_ids(raw_text,"CONTROL")

        # Step 2️⃣ Extract process IDs based on similarity
        process_ids = extract_process_ids_from_rag(
            rag_results,
            min_similarity=0.5
        )

        # ----------------------------
        # CASE A️⃣: No strong semantic intent → VIEW ALL
        # ----------------------------
        if not process_ids:
            payload = {
                "action": "select",
                "table": "control"
            }
            result = call_lambda(payload)
            records = result.get("records", [])

            if not records:
                return "❌ No processes found."

            return format_control_response(records)

        # ----------------------------
        # CASE B️⃣: One or more related processes
        # ----------------------------
        payload = {
            "action": "select",
            "table": "control",
            "where": {
                "control_id": process_ids
            }
        }

        result = call_lambda(payload)
        records = result.get("records", [])

        if not records:
            return "❌ Process found in RAG but missing in database."

        return format_control_response(records)

    except Exception as e:
        return f"❌ Error fetching process data: {e}"



def format_control_response(controls):
    response = "🛡 Control Details\n\n"

    for idx, c in enumerate(controls, start=1):
        response += f"{idx}. 🛡 {c.get('control_name', 'N/A')}\n"

        if c.get("description"):
            response += f"   • Description: {c['description']}\n"
        if c.get("control_type"):
            response += f"   • Control Type: {c['control_type']}\n"
        if c.get("control_category"):
            response += f"   • Category: {c['control_category']}\n"

        response += "\n"

    return response.strip()
