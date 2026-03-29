import chromadb
import os

class MemoryManager:
    def __init__(self):
        path = os.getenv("CHROMA_DB_DIR", "chroma_db")
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("sessions")

    def store(self, session_id: str, content: str):
        self.collection.upsert(ids=[session_id], documents=[content])

    def recall(self, query: str, n_results: int = 20):
        return str(self.collection.query(query_texts=[query], n_results=n_results))