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

def run_view_test_plan_pipeline(intent: str, raw_text: str):
    try:
        # Step 1️⃣ Semantic search (RAG)
        rag_results = rag_find_process_ids(raw_text,"TEST_PLAN")

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
                "table": "test_plan"
            }
            result = call_lambda(payload)
            records = result.get("records", [])

            if not records:
                return "❌ No test paln  found."

            return format_test_plan_response(records)

        # ----------------------------
        # CASE B️⃣: One or more related processes
        # ----------------------------
        payload = {
            "action": "select",
            "table": "test_plan",
            "where": {
                "test_plan_id": process_ids
            }
        }

        result = call_lambda(payload)
        records = result.get("records", [])

        if not records:
            return "❌Test Plan found in RAG but missing in database."

        return format_test_plan_response(records)

    except Exception as e:
        return f"❌ Error fetching test paln data: {e}"


def format_test_plan_response(risks):
    response = "⚠️ Test Plan Created in the System\n\n"

    for idx, r in enumerate(risks, start=1):
        response += f"{idx}. ⚠ {r.get('test_plan_name', 'N/A')}\n"

        if r.get("description"):
            response += f"   • Description: {r['description']}\n"
        if r.get("module"):
            response += f"   • Module: {r['module']}\n"
        if r.get("status"):
            response += f"   • Status: {r['status']}\n"

        response += "\n"

    return response.strip()
