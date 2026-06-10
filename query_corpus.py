import os
from vector_store import VectorStore

def query_corpus(query, n_results=10, where_filter=None):
    store = VectorStore()
    kwargs = {
        "query_texts": [query],
        "n_results": n_results
    }
    if where_filter:
        kwargs["where"] = where_filter

    results = store.collection.query(**kwargs)
    
    with open("query_results.txt", "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\n")
        f.write(f"Filter: {where_filter}\n\n")
        if not results['documents'] or not results['documents'][0]:
            f.write("No results found.\n")
            return
            
        for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
            f.write(f"--- Result {i+1} (Distance: {dist}) ---\n")
            f.write(f"Source: {meta.get('source', 'Unknown')}\n")
            f.write(f"Type: {meta.get('document_type', 'Unknown')}\n")
            f.write(f"Programme: {meta.get('programme', 'Unknown')}\n")
            f.write(f"Content:\n{doc}\n\n")

if __name__ == "__main__":
    prompt = "que linhas de apoio se aplicam a associações sem fins lucrativos, e que ações aqui estas podem fazer para se poderem a candidatar a mais apoios."
    print("Executing Hybrid Query (Filter by Guide)...")
    query_corpus(prompt, n_results=10, where_filter={"document_type": "guide"})
