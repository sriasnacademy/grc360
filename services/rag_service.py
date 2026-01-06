import uuid
import json
from connectors.lambda_pgvector import PGVectorDB
from services.embedding_service import get_embedding

pgvector_db = PGVectorDB(function_name="grc-vectordb")

EXPECTED_DIM = 384

def save_process_to_rag(data: dict):
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

        # 1️⃣ Generate embedding
        embedding = get_embedding(rag_text)

        # 2️⃣ Validate embedding
        if not isinstance(embedding, list):
            raise ValueError("Embedding is not a list")

        if len(embedding) != EXPECTED_DIM:
            raise ValueError(
                f"Invalid embedding size: {len(embedding)} (expected {EXPECTED_DIM})"
            )

        print("✅ Embedding size:", len(embedding))

        # 3️⃣ Convert embedding → pgvector literal
        embedding_str = "[" + ",".join(f"{float(x):.6f}" for x in embedding) + "]"

        print(embedding_str)
        print("✅ Vector string dimensions:",
              embedding_str.count(",") + 1)

        query = """
        INSERT INTO rag_documents (
            id,
            entity_type,
            entity_id,
            content,
            embedding,
            metadata
        )
        VALUES (
            gen_random_uuid(),
            %s,
            %s,
            %s,
            %s::vector,
            %s::jsonb
        );
        """

        params = (
            "PROCESS",
            data.get("process_name"),
            rag_text,
            embedding_str,
            json.dumps({
                "department": data.get("department"),
                "frequency": data.get("frequency"),
                "source": "mysql_processes"
            })
        )

        pgvector_db.execute(query, params)

        print("✅ RAG document inserted successfully")

    except Exception as e:
        print("⚠️ RAG save failed:", str(e))
