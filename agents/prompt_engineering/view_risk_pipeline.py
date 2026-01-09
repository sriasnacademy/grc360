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

def run_view_risk_pipeline(intent: str, raw_text: str):
    try:
        # Step 1️⃣ Semantic search (RAG)
        rag_results = rag_find_process_ids(raw_text,"RISK")

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
                "table": "risk"
            }
            result = call_lambda(payload)
            records = result.get("records", [])

            if not records:
                return "❌ No processes found."

            return format_risk_response(records)

        # ----------------------------
        # CASE B️⃣: One or more related processes
        # ----------------------------
        payload = {
            "action": "select",
            "table": "risk",
            "where": {
                "risk_id": process_ids
            }
        }

        result = call_lambda(payload)
        records = result.get("records", [])

        if not records:
            return "❌ Process found in RAG but missing in database."

        return format_risk_response(records)

    except Exception as e:
        return f"❌ Error fetching process data: {e}"


def format_risk_response(risks):
    response = "⚠️ Risks Created in the System\n\n"

    for idx, r in enumerate(risks, start=1):
        response += f"{idx}. ⚠ {r.get('risk_name', 'N/A')}\n"

        if r.get("description"):
            response += f"   • Description: {r['description']}\n"
        if r.get("impact"):
            response += f"   • Impact: {r['impact']}\n"
        if r.get("likelihood"):
            response += f"   • Likelihood: {r['likelihood']}\n"
        if r.get("severity"):
            response += f"   • Severity: {r['severity']}\n"
        if r.get("owner"):
            response += f"   • Owner: {r['owner']}\n"
        if r.get("status"):
            response += f"   • Status: {r['status']}\n"

        response += "\n"

    return response.strip()
