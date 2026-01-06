from services.embedding_manager import EmbeddingManager

_embedding_manager = EmbeddingManager()

def get_embedding(text: str) -> list[float]:
    return _embedding_manager.generate_embedding(text)
