from connectors.lambda_mysql import call_lambda
from services.rag_retrieval_service import rag_find_process_ids

def extract_process_ids_from_rag(rag_results, min_similarity=0.5):
    """
    Returns process_ids sorted by similarity (high → low)
    """
    if not rag_results:
        return []

    filtered = []
    for r in rag_results:
        similarity = r[4]
        if similarity >= min_similarity:
            try:
                filtered.append((int(r[2]), similarity))
            except ValueError:
                continue

    # sort by similarity desc
    filtered.sort(key=lambda x: x[1], reverse=True)

    return [pid for pid, _ in filtered]

def run_view_process_pipeline(intent: str, raw_text: str):
    try:
        # Step 1️⃣ Semantic search (RAG)
        rag_results = rag_find_process_ids(raw_text,"PROCESS")

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
                "table": "processes"
            }
            result = call_lambda(payload)
            records = result.get("records", [])

            if not records:
                return "❌ No processes found."

            return format_process_response(records)

        # ----------------------------
        # CASE B️⃣: One or more related processes
        # ----------------------------
        payload = {
            "action": "select",
            "table": "processes",
            "where": {
                "process_id": process_ids
            }
        }

        result = call_lambda(payload)
        records = result.get("records", [])

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
