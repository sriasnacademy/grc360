import uuid
import json
from connectors.lambda_pgvector import PGVectorDB
from services.embedding_service import get_embedding

pgvector_db = PGVectorDB(function_name="grc-vectordb")

EXPECTED_DIM = 384

def save_process_to_rag(data: dict, mysql_process_id: int):
    try:
        rag_text = f"""
    Process Name: {data.get('process_name')}
    Description: {data.get('description')}
    Department: {data.get('department')}
    Owner: {data.get('owner')}
    Frequency: {data.get('frequency')}
    Triggers: {', '.join(data.get('triggers', []))}
    Outcomes: {', '.join(data.get('outcomes', []))}
    """.strip()

        embedding = get_embedding(rag_text)
        embedding_str = "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"

        query = """
        INSERT INTO rag_documents (
            id,
            entity_type,
            entity_id,
            content,
            embedding,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb);
        """

        params = (
            str(uuid.uuid4()),
            "PROCESS",
            str(mysql_process_id),  # 🔑 LINK HERE
            rag_text,
            embedding_str,
            json.dumps({
                "source_table": "processes",
                "mysql_id": mysql_process_id
            })
        )

        pgvector_db.execute(query, params)
        print("Rag Inserted Successfully")

    except Exception as e:
        print("⚠️ RAG save failed:", str(e))
