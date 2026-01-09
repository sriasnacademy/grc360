
from services.embedding_service import get_embedding
from connectors.lambda_pgvector import PGVectorDB

def rag_find_process_ids(query: str,entitytype:str, top_k: int = 3):
    embedding = get_embedding(query)
    embedding_str = "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"
    
    query = """
        SELECT id, entity_type,
    entity_id,
    content, 1 - (embedding <=> %s::vector) AS similarity FROM rag_documents
        WHERE entity_type = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
    params = [embedding_str, entitytype, embedding_str, top_k]
    db = PGVectorDB(function_name="grc-vectordb")
    result = db.execute(query,params)
    return result
