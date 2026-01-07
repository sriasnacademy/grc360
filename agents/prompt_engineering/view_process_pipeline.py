from connectors.lambda_mysql import call_lambda
from services.rag_retrieval_service import rag_find_process_ids

def get_best_process_id_from_rag(rag_results, min_similarity=0.7):
    if not rag_results:
        return None

    best_match = rag_results[0]   # already sorted by similarity

    similarity = best_match[4]
    if similarity < min_similarity:
        return None  # low confidence match

    process_id = int(best_match[2])  # entity_id → process_id
    return process_id

def run_view_process_pipeline(intent: str, raw_text: str):
    try:
        # Step 1️⃣ Search in RAG
        rag_results = rag_find_process_ids(raw_text)

        if not rag_results:
            return "❌ No matching process found."

        # rag_results is a LIST
        
        rag_results_dict = [
        {
            "id": r[0],
            "entity_type": r[1],
            "process_id": r[2],
            "content": r[3],
            "similarity": r[4]
        }
        for r in rag_results
        ]
        
        #process_ids = [r["process_id"] for r in rag_results_dict]
        
        correct_process_id = get_best_process_id_from_rag(rag_results)
        
        # Step 2️⃣ Fetch from MySQL
        payload = {
            "action": "select",
            "table": "processes",
            "where": {
                "process_id": correct_process_id
            }
        }

        records = call_lambda(payload)  # ← LIST

        if not records:
            return "❌ Process found in RAG but missing in database."

        return format_process_response(records)

    except Exception as e:
        return f"❌ Error fetching process data: {e}"


# -------------------------------------------------
# Format response for AI assistant UI
# -------------------------------------------------
def format_process_response(processes):
    response = "📋 Process Details\n\n"

    for idx, p in enumerate(processes, start=1):
        response += f"{idx}. 📌 {p.get('process_name', 'N/A')}\n"

        if p.get("department"):
            response += f"   • Department: {p['department']}\n"
        if p.get("process_owner"):
            response += f"   • Owner: {p['process_owner']}\n"
        if p.get("frequency"):
            response += f"   • Frequency: {p['frequency']}\n"
        if p.get("triggers"):
            response += f"   • Triggers: {p['triggers']}\n"
        if p.get("outcomes"):
            response += f"   • Outcomes: {p['outcomes']}\n"
        if p.get("description"):
            response += f"   • Description: {p['description']}\n"

        response += "\n"

    return response.strip()
