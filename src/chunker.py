import re
import uuid

class HierarchicalChunker:
    def __init__(self, max_chunk_size=1000):
        self.max_chunk_size = max_chunk_size

    def chunk_text(self, text, base_metadata):
        """
        Splits text into logical chunks and attaches metadata.
        For now, does a basic paragraph split that respects max_chunk_size.
        Can be enhanced to look for 'Artigo X' or 'Anexo Y'.
        """
        # Junk filters
        spam_patterns = ["página não encontrada", "sítio utiliza cookies", "pedimos-lhe desculpa pela situação", "copyright iapmei"]

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk_text = ""
        
        for p in paragraphs:
            # Cleansing
            p_lower = p.lower()
            if any(spam in p_lower for spam in spam_patterns):
                continue
                
            if len(current_chunk_text) + len(p) > self.max_chunk_size and current_chunk_text:
                if len(current_chunk_text.strip()) > 50:
                    chunks.append(self._create_chunk_dict(current_chunk_text, base_metadata))
                current_chunk_text = p
            else:
                current_chunk_text += "\n\n" + p if current_chunk_text else p
                
        if current_chunk_text and len(current_chunk_text.strip()) > 50:
            chunks.append(self._create_chunk_dict(current_chunk_text, base_metadata))
            
        return chunks
        
    def _create_chunk_dict(self, text, metadata):
        return {
            "id": str(uuid.uuid4()),
            "text": text.strip(),
            "metadata": metadata
        }

import re

class ClassifierTagger:
    def __init__(self):
        # We can implement a local LLM prompt here using OpenAI API (if configured)
        # or local huggingface models to tag the document correctly.
        # For now, we use enhanced heuristics based on filename and content.
        self.categories = {
            "regulation": [r'regulamento', r'portaria', r'decreto', r'diário da república'],
            "manual": [r'manual de procedimentos', r'manual'],
            "guide": [r'guia', r'orientação', r'regras'],
            "form_guide": [r'apoio ao preenchimento', r'formulário'],
            "call_listing": [r'aviso', r'plano anual', r'concursos abertos'],
            "methodology": [r'metodologia', r'seleção de operações', r'handbook'],
            "blog": [r'dicas para', r'tudo o que precisa saber', r'guia completo para empresas'],
            "research": [r'performance of portuguese firms', r'oecd', r'academic']
        }

    def generate_metadata(self, filename, text):
        """
        Generates metadata for the document based on filename/content.
        """
        filename_lower = filename.lower()
        text_lower = text[:5000].lower() # Search in the first 5000 chars

        document_type = "unknown"
        
        # 1. Strong filename heuristics
        if filename_lower.startswith('blog_'):
            document_type = "blog"
        elif filename_lower.startswith('dr_'):
            document_type = "regulation"
        elif "manual" in filename_lower or filename_lower.startswith('mp_'):
            document_type = "manual"
        elif "guia" in filename_lower:
            document_type = "form_guide" if "formul" in filename_lower or "preenchimento" in filename_lower else "guide"
        elif filename_lower.startswith('methodology_'):
            document_type = "methodology"
        elif "aviso" in filename_lower or "plano" in filename_lower:
            document_type = "call_listing"
        else:
            # 2. Fallback to text content checking
            for cat, patterns in self.categories.items():
                if any(re.search(p, text_lower) for p in patterns):
                    document_type = cat
                    break

        programme = "unknown"
        if "2030" in filename_lower or "2030" in text_lower:
            programme = "PT2030"
        elif "prr" in filename_lower or "prr" in text_lower:
            programme = "PRR"

        # Basic version detection
        version_match = re.search(r'versão\s*(\d+[\.\d]*)', text_lower) or re.search(r'v(\d+[\.\d]*)', filename_lower)
        version = version_match.group(1) if version_match else None

        # Effective date detection (naive: looks for YYYY-MM or YYYY-MM-DD or DD/MM/YYYY)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{4}-\d{2})', text_lower)
        effective_date = date_match.group(1) if date_match else None

        return {
            "source": filename,
            "document_type": document_type,
            "programme": programme,
            "version": version,
            "effective_date": effective_date
        }
