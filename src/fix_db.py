import os
from database import init_db, Document
from chunker import ClassifierTagger
from pdf_processor import LocalPyMuPDFProcessor

def fix():
    db = init_db()
    tagger = ClassifierTagger()
    pdf_proc = LocalPyMuPDFProcessor()
    
    docs = db.query(Document).all()
    for doc in docs:
        filepath = os.path.join("data/raw", doc.title)
        if not os.path.exists(filepath):
            continue
            
        full_text = ""
        if filepath.endswith('.pdf'):
            pages = pdf_proc.process_pdf(filepath)
            full_text = "\n\n".join([p["content"] for p in pages])
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                full_text = f.read()
                
        new_meta = tagger.generate_metadata(doc.title, full_text)
        print(f"Updating {doc.title}: {doc.document_type} -> {new_meta['document_type']}")
        doc.document_type = new_meta['document_type']
        
    db.commit()
    print("Done fixing database.")

if __name__ == '__main__':
    fix()
