import uuid
import json
from connectors.lambda_pgvector import PGVectorDB
from services.embedding_service import generate_embedding
from utils.rag_builder import build_process_rag_text


# Initialize once (reuse across calls)
pgvector_db = PGVectorDB(function_name="grc-vectordb")


def save_process_to_rag(data: dict):
    """
    Save process into pgvector AFTER MySQL save.
    Failure here must NOT break main flow.
    """
    try:
        rag_text = build_process_rag_text(data)
        embedding = generate_embedding(rag_text)

        query = """
            INSERT INTO rag_documents (
                id,
                entity_type,
                entity_id,
                content,
                embedding,
                metadata,
                created_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, NOW()
            )
        """

        params = [
            str(uuid.uuid4()),
            "PROCESS",
            data.get("process_name"),
            rag_text,
            embedding,
            json.dumps({
                "department": data.get("department"),
                "frequency": data.get("frequency"),
                "source": "mysql_processes"
            })
        ]

        pgvector_db.execute(query, params)

    except Exception as e:
        # IMPORTANT: RAG is non-blocking
        print("⚠️ RAG save failed:", str(e))
