from connectors.lambda_mysql import call_lambda
from services.rag_retrieval_service import *



def run_view_subprocess_pipeline(intent: str, raw_text: str):
    try:
        # Step 1️⃣ Semantic search (RAG)
        rag_results = rag_find_process_ids(raw_text,"SUB_PROCESS")

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
                "table": "sub_processes"
            }
            result = call_lambda(payload)
            records = result.get("records", [])

            if not records:
                return "❌ No processes found."

            return format_subprocess_response(records)

        # ----------------------------
        # CASE B️⃣: One or more related processes
        # ----------------------------
        payload = {
            "action": "select",
            "table": "sub_processes",
            "where": {
                "sub_process_id": process_ids
            }
        }

        result = call_lambda(payload)
        records = result.get("records", [])

        if not records:
            return "❌ Process found in RAG but missing in database."

        return format_subprocess_response(records)

    except Exception as e:
        return f"❌ Error fetching process data: {e}"


def format_subprocess_response(sub_processes):
    response = "🔹 Sub-Processes Created in the System\n\n"

    for idx, sp in enumerate(sub_processes, start=1):
        response += f"{idx}. 🔸 {sp.get('sub_process_name', 'N/A')}\n"

        if sp.get("process_id"):
            response += f"   • Process ID: {sp['process_id']}\n"
        if sp.get("department"):
            response += f"   • Department: {sp['department']}\n"
        if sp.get("sub_process_owner"):
            response += f"   • Owner: {sp['sub_process_owner']}\n"
        if sp.get("frequency"):
            response += f"   • Frequency: {sp['frequency']}\n"
        if sp.get("status"):
            response += f"   • Status: {sp['status']}\n"
        if sp.get("description"):
            response += f"   • Description: {sp['description']}\n"

        response += "\n"

    return response.strip()
