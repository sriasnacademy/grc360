import json
import uuid

from connectors.lambda_mysql import call_lambda
from connectors.lambda_pgvector import PGVectorDB
from utils.rag_builder import build_rag_payload
from services.embedding_service import get_embedding

# ------------------------------------
# PGVECTOR CLIENT
# ------------------------------------
pgvector = PGVectorDB(
    function_name="grc-vectordb",
    region="ap-south-1"
)

# ------------------------------------
# FETCH PROCESS DATA FROM MYSQL
# ------------------------------------
def fetch_processes_from_mysql():
    payload = {
        "action": "select",
        "table": "processes",
        "query": """
            SELECT
                process_id,
                process_name,
                description,
                department,
                process_owner,
                frequency,
                triggers,
                outcomes
            FROM processes
        """
    }

    response = call_lambda(payload)
    return response.get("records", [])


# ------------------------------------
# INSERT INTO RAG (PGVECTOR)
# ------------------------------------
def insert_processes_into_rag(process_rows):

    insert_sql = "INSERT INTO rag_documents (id,entity_type,entity_id,content,embedding,metadata) VALUES (%s, %s, %s, %s,%s, %s)"


    success = 0
    failed = 0

    for row in process_rows:
        process_id = row.get("process_id")
        description = row.get("description")

        try:
            rag_payload = build_rag_payload("PROCESS", row)
            embeddingstext = get_embedding(description)
            embedding_str = "[" + ",".join(f"{x:.6f}" for x in embeddingstext) + "]"

            params = (
    str(uuid.uuid4()),
    "PROCESS",
    str(process_id),
    rag_payload["rag_text"], embedding_str,        # goes into `content`
    json.dumps(rag_payload["metadata"])
)


            response = pgvector.execute(insert_sql, params)

            rows = response.get("rows_affected", 0)

            print(response)

        except Exception as e:
            failed += 1
            print(f"❌ Failed PROCESS → RAG | process_id={process_id}")
            print(f"   Error: {e}")

    print("\n📊 RAG INSERT SUMMARY")
    print(f"✅ Success: {success}")
    print(f"❌ Failed : {failed}")


# ------------------------------------
# MAIN ENTRY
# ------------------------------------
def ragbuild():
    print("🔄 Fetching process data from MySQL...")
    process_rows = fetch_processes_from_mysql()

    if not process_rows:
        print("⚠️ No process records found")
        return

    print(f"📦 Found {len(process_rows)} process records")

    insert_processes_into_rag(process_rows)

    print("🎯 Process → RAG bulk ingestion completed")
