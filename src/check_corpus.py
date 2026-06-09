import os
from sqlalchemy import create_engine
import pandas as pd
import chromadb

def check_state():
    print("=== CORPUS STATE REPORT ===\n")
    
    # 1. Raw Files
    raw_dir = "data/raw"
    if os.path.exists(raw_dir):
        files = os.listdir(raw_dir)
        print(f"Raw Files ({len(files)} downloaded):")
        for f in files:
            print(f"  - {f}")
    else:
        print("Raw Files: Directory not found.")

    # 2. SQLite Database
    try:
        engine = create_engine("sqlite:///db/corpus.db")
        df_docs = pd.read_sql("SELECT * FROM documents", engine)
        df_calls = pd.read_sql("SELECT * FROM calls", engine)
        
        print(f"\nSQLite Database (Structured Metadata):")
        print(f"  > Documents Table: {len(df_docs)} records")
        if len(df_docs) > 0:
            print("    " + df_docs[['title', 'document_type']].to_string(index=False).replace('\n', '\n    '))
            
        print(f"\n  > Calls (Avisos) Table: {len(df_calls)} records")
        if len(df_calls) > 0:
            print("    " + df_calls[['call_code', 'status', 'budget']].to_string(index=False).replace('\n', '\n    '))
    except Exception as e:
        print(f"\nError querying SQLite: {e}")

    # 3. ChromaDB Vector Store
    try:
        client = chromadb.PersistentClient(path="db/chroma_db")
        col = client.get_collection("portugal_2030_corpus")
        print(f"\nChromaDB Vector Store:")
        print(f"  > Indexed Knowledge Chunks: {col.count()}")
    except Exception as e:
        print(f"\nError querying ChromaDB: {e}")

if __name__ == "__main__":
    check_state()
