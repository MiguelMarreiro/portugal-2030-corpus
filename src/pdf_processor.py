import fitz  # PyMuPDF
import os

class BasePDFProcessor:
    def process_pdf(self, filepath):
        raise NotImplementedError

class LocalPyMuPDFProcessor(BasePDFProcessor):
    def __init__(self):
        pass

    def process_pdf(self, filepath):
        """
        Extracts text from a PDF file using PyMuPDF.
        Returns a list of dictionaries, each representing a page.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PDF not found: {filepath}")

        doc = fitz.open(filepath)
        pages = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            pages.append({
                "page": page_num + 1,
                "content": text
            })
        return pages

class OpenAIPDFProcessor(BasePDFProcessor):
    def __init__(self):
        # Placeholder for OpenAI Vision or specialized parsing
        pass
    
    def process_pdf(self, filepath):
        print(f"OpenAIPDFProcessor invoked for {filepath} - Fallback not fully implemented yet.")
        # E.g., convert PDF to images, send to GPT-4o, get markdown
        return [{"page": 1, "content": "Placeholder OpenAI parsed content"}]

class LlamaParseProcessor(BasePDFProcessor):
    def __init__(self):
        # Optional modular backend for complex PDFs
        self.api_key = os.environ.get("LLAMA_CLOUD_API_KEY")
        if self.api_key:
            from llama_parse import LlamaParse
            self.parser = LlamaParse(
                result_type="markdown",
                parsing_instruction="Extract tables accurately keeping their row and column structure."
            )
        else:
            self.parser = None

    def process_pdf(self, filepath):
        if not self.parser:
            print("LLAMA_CLOUD_API_KEY not found. Falling back to local PyMuPDF.")
            return LocalPyMuPDFProcessor().process_pdf(filepath)
            
        print(f"Processing {filepath} with LlamaParse...")
        try:
            # Sync execution for now
            documents = self.parser.load_data(filepath)
            # Combine all documents into a single chunk or page representation
            content = "\n\n".join([doc.text for doc in documents])
            return [{"page": 1, "content": content}]
        except Exception as e:
            print(f"LlamaParse failed: {e}. Falling back to local PyMuPDF.")
            return LocalPyMuPDFProcessor().process_pdf(filepath)


if __name__ == "__main__":
    processor = LocalPyMuPDFProcessor()
    # Test would go here
