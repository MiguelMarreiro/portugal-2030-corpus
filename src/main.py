import os
from database import init_db, Document
from vector_store import VectorStore
from crawlers import StaticCrawler, DynamicCallTracker, DiarioDaRepublicaSpider, IapmeiSpider, PrrSpider, BalcaoFundosSpider, AcademicResearchSpider, BlogSpider, MethodologySpider
from pdf_processor import LocalPyMuPDFProcessor
from html_processor import HTMLProcessor
from chunker import HierarchicalChunker, ClassifierTagger

def main():
    print("Starting Portugal 2030 & PRR Corpus Pipeline...")
    
    # 1. Initialize DB and Vector Store
    db_session = init_db()
    vector_store = VectorStore()
    
    # 2. Run Dynamic Call Tracker (Daily Run Context)
    tracker = DynamicCallTracker(db_session)
    tracker.fetch_compete_avisos()
    tracker.fetch_norte2030_avisos()
    
    # Phase 2 & 4: Full Corpus Scaling (Crawler Upgrades)
    
    # 1. Diário da República
    dr_spider = DiarioDaRepublicaSpider()
    portarias = [
        "https://diariodarepublica.pt/dr/legislacao-consolidada/portaria/2023-215139683-215140684",
        "https://diariodarepublica.pt/dr/detalhe/portaria/103-a-2023-211029413"
    ]
    for url in portarias:
        dr_spider.scrape_legislation(url)

    # 2. IAPMEI
    iapmei = IapmeiSpider()
    iapmei.scrape_concursos()
    iapmei_info_targets = [
        "https://www.iapmei.pt/PRODUTOS-E-SERVICOS/Qualificacao-Certificacao/Certificacao-PME/Certificacao-PME.aspx",
        "https://www.iapmei.pt/PRODUTOS-E-SERVICOS/Qualificacao-Certificacao/Certificacao-PME/Manual-de-Certificacao-PME.aspx",
        "https://www.iapmei.pt/PRODUTOS-E-SERVICOS/Qualificacao-Certificacao/Certificacao-PME/FAQ-Certificacao-PME.aspx",
        "https://www.iapmei.pt/PRODUTOS-E-SERVICOS/Qualificacao-Certificacao/Estatuto-PME-Lider/Estatuto-PME-Lider.aspx",
        "https://www.iapmei.pt/PRODUTOS-E-SERVICOS/Qualificacao-Certificacao/Certificacao-PME/Guia-Pratico.aspx"
    ]
    iapmei.scrape_info_pages(iapmei_info_targets)

    # 3. PRR
    prr = PrrSpider()
    prr_targets = [
        "https://recuperarportugal.gov.pt/candidaturas-prr/", 
        "https://recuperarportugal.gov.pt/wp-content/uploads/2023/11/Manual-de-Procedimentos-5.a-Edicao-Versao-3.pdf",
        "https://recuperarportugal.gov.pt/wp-content/uploads/2023/01/MP_4aEdicao_vf_20-01-2023-003.pdf",
        "https://www.portaldahabitacao.pt/documents/20126/3675179/Manual_Medidas_PRR_Benefici%C3%A1rios+(2).pdf"
    ]
    prr.fetch_manuals(prr_targets)

    # 4. Balcão dos Fundos
    balcao = BalcaoFundosSpider()
    balcao.scrape_faq()

    academic = AcademicResearchSpider()
    research_targets = [
        "https://www.oecd.org/content/dam/oecd/en/publications/reports/2023/oecd-economic-surveys-portugal-2023_19934255/1247076d-en.pdf",
        "https://www.planapp.gov.pt/wp-content/uploads/2023/07/re202301_en.pdf"
    ]
    academic.fetch_research(research_targets)

    # 6. Blogs & Best Practices
    blog_spider = BlogSpider()
    blog_targets = [
        "https://estrategor.pt/qualificacao-das-pme-5-dicas-para-se-candidatar-ao-portugal-2030/",
        "https://dualup.pt/financiamento-portugal-2030-guia-completo-para-empresas-e-pme/",
        "https://bizcenter.pt/portugal-2030/",
        "https://www.sage.com/pt-pt/blog/fundos-europeus-para-empresas/",
        "https://www.efacont.pt/candidatura-apoios/"
    ]
    for url in blog_targets:
        blog_spider.scrape_blog(url)

    # 7. Methodologies & Handbooks
    methodology_spider = MethodologySpider()
    methodology_targets = [
        "https://archive.interact.eu/download/file/fid/4427",
        "https://www.iapmei.pt/PRODUTOS-E-SERVICOS/Incentivos-Financiamento/Documentos-Incentivos/KN-03-23-121-EN-N.aspx"
    ]
    methodology_spider.fetch_methodologies(methodology_targets)

    # 3. Process all downloaded PDF files from the local raw directory
    pdf_processor = LocalPyMuPDFProcessor()
    chunker = HierarchicalChunker()
    tagger = ClassifierTagger()
    
    raw_dir = "data/raw"
    files_to_process = []
    if os.path.exists(raw_dir):
        files_to_process.extend([os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith('.pdf')])
        # Also include text files from blogs/dynamic spiders
        files_to_process.extend([os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith('.txt')])

    for filepath in files_to_process:
        print(f"Processing downloaded file: {filepath}")
        try:
            if filepath.endswith('.pdf'):
                pages = pdf_processor.process_pdf(filepath)
                full_text = "\n\n".join([p["content"] for p in pages])
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    full_text = f.read()
            
            # 4. Metadata and Chunking
            filename = os.path.basename(filepath)
            base_metadata = tagger.generate_metadata(filename, full_text)
            chunks = chunker.chunk_text(full_text, base_metadata)
            
            # 5. Index into Vector Store
            vector_store.add_chunks(chunks)
            print(f"Indexed {len(chunks)} chunks from {filename}")
            
            # 6. Save to DB
            doc_record = Document(
                title=filename,
                source_url=filename, # In a real scenario we'd track the original URL
                local_path=filepath,
                document_type=base_metadata.get("document_type", "unknown"),
                programme=base_metadata.get("programme", "unknown")
            )
            existing_doc = db_session.query(Document).filter_by(source_url=filename).first()
            if not existing_doc:
                db_session.add(doc_record)
                db_session.commit()
                print(f"Document {filename} metadata saved to SQLite.")
            else:
                print(f"Document {filename} already exists in SQLite.")
                
        except Exception as e:
            print(f"Failed to process document {filepath}: {e}")

if __name__ == "__main__":
    main()
