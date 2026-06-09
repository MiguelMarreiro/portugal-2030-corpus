# Portugal 2030 & PRR Funding Assistant

This project is an automated pipeline and RAG (Retrieval-Augmented Generation) assistant designed to scrape, structure, and query regulatory documents, manuals, and calls (Avisos) for the Portugal 2030 and PRR funding frameworks.

## Project Structure
- `src/crawlers.py`: Contains specific spiders for Diário da República, IAPMEI, Recuperar Portugal (PRR), and Balcão dos Fundos.
- `src/html_processor.py` & `src/pdf_processor.py`: Extracts text from scraped HTML and PDF files (using PyMuPDF).
- `src/chunker.py`: Slices documents into logical semantic blocks and uses a local model (via SentenceTransformers) to assign metadata.
- `src/vector_store.py`: Manages the local `ChromaDB` instance for fast semantic retrieval.
- `src/database.py`: Manages the local `SQLite` database (`corpus.db`) to track structured data like open calls (Avisos) and document metadata.
- `src/rag_core.py`: Connects the ChromaDB vector store to the local LLM (`Ollama` running `llama3`).
- `src/assistant_app.py`: The `Streamlit` web interface for chatting with the Funding Assistant.
- `src/main.py`: The central orchestrator script that runs the crawlers, processes new PDFs in `data/raw`, and indexes them.

## Data Flow
1. **Scraping**: `main.py` triggers the spiders to download PDFs into `data/raw/`.
2. **Processing**: `main.py` iterates over `data/raw/`, extracts text, chunks it, and indexes it into `ChromaDB` and `SQLite`.
3. **Querying**: The Streamlit app (`assistant_app.py`) queries ChromaDB for context and uses Ollama to generate answers.

## How to Run the Assistant
Ensure you have the local model downloaded first:
```bash
ollama pull llama3
```
Then, activate the virtual environment and start the web app:
```bash
# Windows / Git Bash
source venv/Scripts/activate
streamlit run src/assistant_app.py
```

## How to Update the Corpus
To trigger a new scrape and re-index newly downloaded files:
```bash
source venv/Scripts/activate
python src/main.py
```
