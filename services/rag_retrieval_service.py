from services.embedding_service import get_embedding
from connectors.lambda_pgvector import PGVectorDB
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_RAG_SERVICE,
)


def rag_find_process_ids(query: str, entitytype: str, top_k: int = 3):
    embedding     = get_embedding(query)
    embedding_str = "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"

    sql_query = """
        SELECT id, entity_type, entity_id, content,
               1 - (embedding <=> %s::vector) AS similarity
        FROM rag_documents
        WHERE entity_type = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    params = [embedding_str, entitytype, embedding_str, top_k]
    db     = PGVectorDB(function_name="grc-vectordb")
    result = db.execute(sql_query, params)

    # ── Attribution record ──────────────────────────────────────────
    hits = result or []
    top_scores = [round(r[4], 3) for r in hits] if hits else []
    attribution_agent.record(
        action_type      = ActionType.RAG_RETRIEVAL,
        actor            = ACTOR_RAG_SERVICE,
        sources          = [
            Source("rag-query", "RAG Query",        "text",     query,           excerpt=query[:200]),
            Source("rag-db",    "pgvector RAG DB",  "database", "rag_documents", excerpt=f"entity_type={entitytype}"),
        ],
        decision_summary = f"RAG retrieved {len(hits)} result(s) for entity_type='{entitytype}' (top_k={top_k})",
        reasoning        = f"Cosine similarity search. Top similarity scores: {top_scores}",
        confidence       = ConfidenceLevel.HIGH if hits else ConfidenceLevel.LOW,
        tags             = ["rag", "retrieval", entitytype.lower()],
    )
    # ────────────────────────────────────────────────────────────────

    return result


def extract_process_ids_from_rag_for_duplicate_check(rag_results, min_similarity=0.7):
    if not rag_results:
        return []
    filtered = []
    for r in rag_results:
        if r[4] >= min_similarity:
            try:
                filtered.append((int(r[2]), r[4]))
            except ValueError:
                continue
    filtered.sort(key=lambda x: x[1], reverse=True)
    return [pid for pid, _ in filtered]


def extract_process_ids_from_rag(rag_results, min_similarity=0.5):
    if not rag_results:
        return []
    filtered = []
    for r in rag_results:
        if r[4] >= min_similarity:
            try:
                filtered.append((int(r[2]), r[4]))
            except ValueError:
                continue
    filtered.sort(key=lambda x: x[1], reverse=True)
    return [pid for pid, _ in filtered]
