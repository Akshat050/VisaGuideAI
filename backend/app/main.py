import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, VisaRequirement, VisaQA
from app.models import ChatRequest, ChatResponse
from app.ai_engine import ai_engine
from app.profile_matcher import profile_matcher
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="VisaGuide AI API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for requests
class ProfileRequest(BaseModel):
    source_country: str
    residence_country: Optional[str] = None
    destination_country: str
    employment_status: str = "employed"

@app.get("/")
def root():
    return {"message": "VisaGuide AI API v2.0", "status": "running"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhealthy: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        response = ai_engine.get_response(
            question=request.message,
            visa_type=request.visa_type,
            session_id=session_id,
            db=db
        )
        return response
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Profile/Country endpoints
@app.get("/api/countries")
def get_available_countries(db: Session = Depends(get_db)):
    """Get all available source and destination countries"""
    try:
        return profile_matcher.get_available_countries(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/get-requirements")
def get_requirements(request: ProfileRequest, db: Session = Depends(get_db)):
    """Get personalized visa requirements based on user profile"""
    try:
        result = profile_matcher.get_personalized_requirements(
            db=db,
            source_country=request.source_country,
            residence_country=request.residence_country,
            destination_country=request.destination_country,
            employment_status=request.employment_status
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visa-info/{visa_type}")
def get_visa_info(visa_type: str, db: Session = Depends(get_db)):
    visa_data = db.query(VisaRequirement).filter(VisaRequirement.visa_type == visa_type).first()
    if not visa_data:
        raise HTTPException(status_code=404, detail="Visa type not found")
    
    return {
        "visa_type": visa_type,
        "visa_info": visa_data.requirements.get('visa_info', {}),
        "required_documents": visa_data.requirements.get('required_documents', []),
        "common_questions": visa_data.requirements.get('common_questions', []),
        "last_updated": str(visa_data.last_verified_date)
    }

@app.get("/api/quick-questions/{visa_type}")
def get_quick_questions(visa_type: str, db: Session = Depends(get_db)):
    questions = db.query(VisaQA).filter(VisaQA.visa_type == visa_type).limit(10).all()
    return {
        "visa_type": visa_type,
        "questions": [{"question": q.question, "answer": q.answer, "category": q.category} for q in questions]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
