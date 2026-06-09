import os
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, persist_directory="db/chroma_db"):
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Using the default embedding function (all-MiniLM-L6-v2) for now.
        # It's local and fast. Later we can swap with OpenAI embeddings if needed.
        self.collection = self.client.get_or_create_collection(
            name="portugal_2030_corpus",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks):
        """
        Add chunks to the vector database.
        chunks is a list of dicts: {"id": str, "text": str, "metadata": dict}
        """
        if not chunks:
            return

        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search(self, query_text, n_results=5, filter_dict=None):
        """
        Search for relevant chunks.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_dict
        )
        return results

if __name__ == "__main__":
    # Test initialization
    vs = VectorStore()
    print(f"Vector store initialized with {vs.collection.count()} chunks.")
