import google.generativeai as genai
from sqlalchemy.orm import Session
from app.database import VisaRequirement, VisaQA, AICallLog
from app.cache import cache
from app.models import ChatResponse
import os
import time

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class AIEngine:
    def __init__(self):
        # Use the latest Gemini 2.5 Flash model
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Using model: gemini-2.5-flash")
    
    def get_response(self, question: str, visa_type: str, session_id: str, db: Session) -> ChatResponse:
        # TIER 1: Database exact match
        exact_match = self._check_exact_qa(question, visa_type, db)
        if exact_match:
            print(f"✅ Database match for: {question}")
            return ChatResponse(response=exact_match['answer'], source='database', cached=False, visa_type=visa_type)
        
        # TIER 2: Cache
        cache_key = f"ai:{cache.hash_question(question, visa_type)}"
        cached = cache.get(cache_key)
        if cached:
            print(f"✅ Cache hit for: {question}")
            return ChatResponse(response=cached, source='cache', cached=True, visa_type=visa_type)
        
        # TIER 3: Generate with AI
        print(f"🤖 Generating AI response for: {question}")
        ai_response = self._generate_ai_response(question, visa_type, session_id, db)
        cache.set(cache_key, ai_response, 86400)
        
        return ChatResponse(response=ai_response, source='ai', cached=False, visa_type=visa_type)
    
    def _check_exact_qa(self, question: str, visa_type: str, db: Session):
        q_lower = question.lower().strip()
        remove_words = ['what', 'is', 'the', 'a', 'an', 'how', 'much', 'do', 'i', 'need', 'can', 'should', '?', 'please', 'tell', 'me']
        q_keywords = ' '.join([word for word in q_lower.split() if word not in remove_words])
        
        qa_list = db.query(VisaQA).filter(VisaQA.visa_type == visa_type).all()
        for entry in qa_list:
            entry_lower = entry.question.lower()
            entry_keywords = ' '.join([word for word in entry_lower.split() if word not in remove_words])
            
            # Check if keywords match
            if q_keywords and (q_keywords in entry_keywords or entry_keywords in q_keywords):
                entry.view_count += 1
                db.commit()
                return {'answer': entry.answer, 'category': entry.category}
        
        return None
    
    def _generate_ai_response(self, question: str, visa_type: str, session_id: str, db: Session) -> str:
        visa_data = db.query(VisaRequirement).filter(VisaRequirement.visa_type == visa_type).first()
        if not visa_data:
            return "I don't have information about this visa type. Please ask about US B1/B2 tourist visa."
        
        requirements = visa_data.requirements
        prompt = self._build_prompt(question, requirements)
        
        start_time = time.time()
        try:
            print(f"🌐 Calling Gemini API...")
            response = self.model.generate_content(prompt)
            processing_time = int((time.time() - start_time) * 1000)
            print(f"✅ Gemini responded in {processing_time}ms")
            
            # Log the call
            input_tokens = int(len(prompt.split()) * 1.3)
            output_tokens = int(len(response.text.split()) * 1.3)
            cost = ((input_tokens / 1_000_000) * 0.075) + ((output_tokens / 1_000_000) * 0.30)
            
            self._log_ai_call(session_id, 'gemini-2.5-flash', input_tokens, output_tokens, f"{cost:.6f}", processing_time, db)
            
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return self._fallback_response(question, requirements)
    
    def _build_prompt(self, question: str, requirements: dict) -> str:
        visa_info = requirements.get('visa_info', {})
        documents = requirements.get('required_documents', [])[:7]
        qa_data = requirements.get('common_questions', [])[:5]
        
        docs = "\n".join([
            f"- {d['name']}: {'MANDATORY' if d.get('mandatory') else 'Optional'}\n  {d.get('requirements', '')}"
            for d in documents
        ])
        
        qa = "\n\n".join([
            f"Q: {q['question']}\nA: {q.get('detailed_answer', q.get('short_answer', ''))}"
            for q in qa_data
        ])
        
        return f"""You are VisaGuide AI, an expert US visa documentation assistant.

VERIFIED DATA (Last updated: {visa_info.get('last_updated', 'Dec 2024')}):

VISA TYPE: {visa_info.get('type', 'US B1/B2 Tourist Visa')}
FEE: ${visa_info.get('fee_usd', 185)} USD (non-refundable)
PROCESSING TIME: {visa_info.get('typical_processing_time', '3-5 weeks')}
APPROVAL RATE: {visa_info.get('approval_rate_india', '75-80%')}

REQUIRED DOCUMENTS:
{docs}

REFERENCE Q&A:
{qa}

USER QUESTION: {question}

INSTRUCTIONS:
- Provide a clear, specific answer based on the verified data above
- Use bullet points for lists
- Highlight critical requirements with ⚠️
- Be encouraging and helpful
- If the data doesn't cover the exact question, provide general visa advice and suggest checking official sources
- Keep response concise (2-4 paragraphs max)

Answer:"""
    
    def _fallback_response(self, question: str, requirements: dict) -> str:
        visa_info = requirements.get('visa_info', {})
        return f"""I'm experiencing technical difficulties, but here's what I can tell you:

**US B1/B2 Tourist Visa Basics:**
- Fee: ${visa_info.get('fee_usd', 185)} USD (non-refundable)
- Processing: {visa_info.get('typical_processing_time', '3-5 weeks')}
- Approval Rate: {visa_info.get('approval_rate_india', '75-80%')}

For your specific question about "{question}", I recommend checking the official source:
{visa_info.get('official_source', 'https://travel.state.gov/')}

Please try asking again in a moment, or rephrase your question."""
    
    def _log_ai_call(self, session_id: str, model: str, input_tokens: int, output_tokens: int, cost_usd: str, processing_time_ms: int, db: Session):
        try:
            log = AICallLog(
                session_id=session_id,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                processing_time_ms=processing_time_ms
            )
            db.add(log)
            db.commit()
            print(f"💰 AI call logged: ${cost_usd} ({input_tokens}→{output_tokens} tokens)")
        except Exception as e:
            print(f"⚠️  Failed to log: {e}")

ai_engine = AIEngine()
