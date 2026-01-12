# embedding_singleton.py
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

_shared_embedding_model = None

def get_shared_embedding():
    global _shared_embedding_model
    if _shared_embedding_model is None:
        _shared_embedding_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
    return _shared_embedding_model
