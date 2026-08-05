import chromadb
import os
import uuid

class MemoryManager:
    def __init__(self):
        path = os.getenv("CHROMA_DB_DIR", "chroma_db")
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("sessions")

    def store(self, session_id: str, content: str):
        doc_id = f"{session_id}-{uuid.uuid4()}"
        self.collection.upsert(ids=[doc_id], documents=[content])

    def recall(self, query: str, n_results: int = 20):
        response = self.collection.query(query_texts=[query], n_results=n_results)
        documents = response['documents'][0] if response['documents'] else None
        distances = response['distances'][0] if response['distances'] else None
        if documents and distances:
            size = len(documents)
            result_dict = {}
            for i in range(size):
                result_dict[documents[i]] = distances[i]
            return str(result_dict)
        return "No Memories Found."