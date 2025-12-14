# Update database.py with the correct DATABASE_URL
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Use environment variable or default to correct connection string
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://visaguide:visaguide123@127.0.0.1:5432/visaguide_db')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class VisaRequirement(Base):
    __tablename__ = 'visa_requirements'
    
    id = Column(Integer, primary_key=True, index=True)
    visa_type = Column(String, index=True)
    source_country = Column(String, default='India')
    destination_country = Column(String, default='USA')
    requirements = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified_date = Column(DateTime, default=datetime.utcnow)

class VisaQA(Base):
    __tablename__ = 'visa_qa'
    
    id = Column(Integer, primary_key=True, index=True)
    visa_type = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)
    category = Column(String)
    source_country = Column(String, default='India')
    created_at = Column(DateTime, default=datetime.utcnow)

class CountryProfile(Base):
    __tablename__ = 'country_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(String, unique=True, index=True)
    source_country = Column(String, index=True)
    source_country_code = Column(String)
    residence_country = Column(String, index=True)
    destination_country = Column(String, index=True)
    destination_code = Column(String)
    visa_type = Column(String, index=True)
    visa_name = Column(String)
    employment_status = Column(String)
    
    # JSON fields
    requirements = Column(JSON)
    interview_details = Column(JSON)
    success_factors = Column(JSON)
    rejection_reasons = Column(JSON)
    country_specific_tips = Column(JSON)
    timeline = Column(JSON)
    quick_facts = Column(JSON)
    
    # Metadata
    verification_status = Column(String)
    last_verified = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    enabled = Column(Boolean, default=True)

class AICallLog(Base):
    __tablename__ = 'ai_call_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    model = Column(String)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost_usd = Column(String)
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

if __name__ == "__main__":
    init_db()