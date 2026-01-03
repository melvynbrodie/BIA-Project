
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True)  # Ticker or UUID
    name = Column(String, nullable=False)
    sector = Column(String)
    country = Column(String, default="India")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    filings = relationship("Filing", back_populates="company")
    financials_annual = relationship("FinancialAnnual", back_populates="company")
    financials_quarterly = relationship("FinancialQuarterly", back_populates="company")
    chunks = relationship("DocumentChunk", back_populates="company")

class Filing(Base):
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, ForeignKey("companies.id"))
    period = Column(String) # e.g., "FY23", "Q1FY24"
    filing_type = Column(String) # "Annual Report", "Quarterly Result"
    source_url = Column(String)
    storage_path = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="filings")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, ForeignKey("companies.id"))
    filing_id = Column(Integer, ForeignKey("filings.id"))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768)) # Dimension for text-embedding-004
    metadata_json = Column(JSON) # Page number, section, etc.
    
    company = relationship("Company", back_populates="chunks")

# Placeholder for structured financials - to be expanded based on Schedule III
class FinancialAnnual(Base):
    __tablename__ = "financials_annual"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, ForeignKey("companies.id"))
    year = Column(Integer)
    revenue = Column(Float)
    ebitda = Column(Float)
    pat = Column(Float)
    # Add full Schedule III fields later
    
    company = relationship("Company", back_populates="financials_annual")

class FinancialQuarterly(Base):
    __tablename__ = "financials_quarterly"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String, ForeignKey("companies.id"))
    quarter = Column(String) # Q1, Q2...
    year = Column(Integer)
    revenue = Column(Float)
    pat = Column(Float)
    
    company = relationship("Company", back_populates="financials_quarterly")
