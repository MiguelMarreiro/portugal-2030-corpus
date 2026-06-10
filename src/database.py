import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
import enum

Base = declarative_base()

class DocumentCategory(enum.Enum):
    REGULATION = "regulation"
    MANUAL = "manual"
    GUIDE = "guide"
    FORM_GUIDE = "form_guide"
    CALL_LISTING = "call_listing"
    METHODOLOGY = "methodology"
    BLOG = "blog"
    RESEARCH = "research"
    UNKNOWN = "unknown"

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    source_url = Column(String, nullable=False) # Removed unique=True to allow multiple versions
    publish_date = Column(DateTime, nullable=True)
    effective_date = Column(DateTime, nullable=True) # Added for versioning
    version = Column(String, nullable=True) # Added for versioning
    programme = Column(String) # PT2030, PRR, EU
    language = Column(String, default="pt")
    instrument_scope = Column(String)
    document_type = Column(String, default="unknown")
    local_path = Column(String) # path to downloaded raw file
    processed_path = Column(String) # path to processed json/md file
    created_at = Column(DateTime, default=datetime.utcnow)

class Call(Base):
    __tablename__ = 'calls'

    id = Column(Integer, primary_key=True)
    call_code = Column(String, unique=True, nullable=False) # Aviso ID
    title = Column(String)
    instrument = Column(String)
    status = Column(String) # Aberto, Fechado, Em Análise, etc.
    open_date = Column(DateTime, nullable=True)
    close_date = Column(DateTime, nullable=True)
    budget = Column(String)
    link = Column(String) # URL to details or PDF
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db(db_path="sqlite:///db/corpus.db"):
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    # Test initialization
    os.makedirs("../db", exist_ok=True)
    session = init_db()
    print("Database initialized successfully.")
