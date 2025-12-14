from app.database import CountryProfile
from app.cache import cache
import hashlib
import os
from dotenv import load_dotenv
import google.generativeai as genai


class AIEngine:
    def __init__(self, model):
        self.model = model

    def get_response(
        self,
        question: str,
        visa_type: str,
        session_id: str,
        db,
        profile_id: str = None,
        source_country: str = None,
        destination_country: str = None,
    ):
        question_clean = question.strip()

        # 0️⃣ No route context → user must select route
        if not profile_id and not (source_country and destination_country):
            return {
                "response": (
                    "Please select your citizenship and destination first so I can "
                    "guide you accurately for your visa."
                ),
                "source": "system",
                "cached": False,
                "visa_type": visa_type,
            }

        # 1️⃣ Load CountryProfile if available
        profile = None
        if profile_id:
            profile = (
                db.query(CountryProfile)
                .filter(CountryProfile.profile_id == profile_id)
                .first()
            )

        # 2️⃣ Cache key (question + route)
        cache_key = hashlib.sha256(
            f"{question_clean}|{profile_id}|{source_country}|{destination_country}".encode()
        ).hexdigest()

        cached = cache.get(cache_key)
        if cached:
            return {
                "response": cached,
                "source": "cache",
                "cached": True,
                "visa_type": visa_type,
            }

        # 3️⃣ Build AI grounding context
        context = self._build_context(profile, source_country, destination_country)

        # 4️⃣ AI answer (NEVER blocked)
        ai_response = self._ask_ai(question_clean, context)

        # 5️⃣ Cache response
        cache.set(cache_key, ai_response)

        return {
            "response": ai_response,
            "source": "ai",
            "cached": False,
            "visa_type": visa_type,
        }

    def _build_context(
        self,
        profile: CountryProfile | None,
        source_country: str | None,
        destination_country: str | None,
    ):
        if not profile:
            return f"""
You are a visa assistant.

Known route:
- Citizenship: {source_country}
- Destination: {destination_country}

Rules:
- Explain application steps and forms clearly
- Do NOT invent required documents
- If unsure about a requirement, say so
- Always advise verifying with official government sources
"""

        return f"""
You are a visa assistant.

Verified route:
- Citizenship: {profile.source_country}
- Destination: {profile.destination_country}
- Visa: {profile.visa_name} ({profile.visa_type})

Verified requirements (authoritative):
Mandatory documents:
{profile.requirements.get('mandatory', [])}

Recommended documents:
{profile.requirements.get('recommended', [])}

Not required:
{profile.requirements.get('not_required', [])}

Interview details:
{profile.interview}

Timeline:
{profile.timeline}

Rules:
- Requirements above are authoritative
- You MAY explain application steps, forms (e.g., DS-160), interviews, timelines
- Do NOT invent new required documents
- Be clear, structured, and practical
- Always advise verifying with official government sources
"""

    def _ask_ai(self, question: str, context: str):
        prompt = f"""
{context}

User question:
{question}

Answer clearly and step-by-step where applicable.
"""
        response = self.model.generate_content(prompt)
        return response.text.strip()


# ✅ Export ai_engine so main.py can import it
load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) in .env")

genai.configure(api_key=API_KEY)
_model = genai.GenerativeModel(MODEL_NAME)

ai_engine = AIEngine(_model)
