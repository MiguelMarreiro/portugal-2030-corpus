import chromadb
from vector_store import VectorStore
import ollama

class RagEngine:
    def __init__(self, model_name="llama3"):
        self.vector_store = VectorStore(persist_directory="db/chroma_db")
        self.model_name = model_name

    def retrieve_context(self, query, n_results=5):
        """
        Retrieves relevant chunks from ChromaDB based on the user's query.
        """
        results = self.vector_store.search(query, n_results=n_results)
        
        if not results or not results['documents'] or not results['documents'][0]:
            return []

        # results['documents'][0] contains the matched texts
        # results['metadatas'][0] contains the associated metadata
        
        contexts = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            source = meta.get("source", "Unknown Source")
            prog = meta.get("programme", "Unknown Programme")
            contexts.append(f"[{prog} - {source}]:\n{doc}")
            
        return contexts

    def generate_answer(self, query, contexts):
        """
        Uses Ollama to generate an answer based strictly on the retrieved context.
        """
        system_prompt = (
            "You are an expert Funding Assistant for Portugal 2030 and the PRR (Plano de Recuperação e Resiliência).\n"
            "Your task is to answer the user's question based strictly on the provided context documents.\n"
            "Do not hallucinate. If the answer is not in the context, say you don't know.\n"
            "Always cite the source of your information using the tags provided in the context.\n"
            "Reply in Portuguese."
        )

        context_block = "\n\n---\n\n".join(contexts)
        
        user_prompt = (
            f"Context Documents:\n{context_block}\n\n"
            f"User Question: {query}\n\n"
            f"Answer:"
        )

        # Call local Ollama model
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}. Make sure Ollama is running and the model '{self.model_name}' is installed."

    def query(self, user_query):
        contexts = self.retrieve_context(user_query)
        if not contexts:
            return "Não encontrei informação relevante na base de dados sobre essa questão."
            
        answer = self.generate_answer(user_query, contexts)
        return answer
