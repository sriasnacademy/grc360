import uuid
import json
from connectors.lambda_pgvector import PGVectorDB
from services.embedding_service import get_embedding
from utils.rag_builder import build_rag_payload

pgvector_db = PGVectorDB(function_name="grc-vectordb")

EXPECTED_DIM = 384

def save_process_to_rag(entity_type: str, data: dict, mysql_id):
    try:
        
        payload = build_rag_payload(entity_type, data)

        embedding = get_embedding(payload["rag_text"])
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
            entity_type,
            str(mysql_id),
            payload["rag_text"],
            embedding_str,
            json.dumps({
                "source_table": payload["source_table"],
                **payload["metadata"]
            })
        )

        pgvector_db.execute(query, params)

        print("Rag Inserted Successfully")

    except Exception as e:
        print("⚠️ RAG save failed:", str(e))
