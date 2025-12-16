import os
import hashlib
from typing import Optional, Any, Dict

import google.generativeai as genai
from dotenv import load_dotenv

from app.database import CountryProfile
from app.cache import cache

load_dotenv()


class AIEngine:
    def __init__(self, model):
        self.model = model

    def get_response(
        self,
        question: str,
        visa_type: Optional[str],
        session_id: str,
        db,
        profile_id: Optional[str] = None,
        source_country: Optional[str] = None,
        residence_country: Optional[str] = None,
        destination_country: Optional[str] = None,
        employment_status: Optional[str] = None,  # ✅ accept it (main.py sends it)
        **kwargs,  # ✅ swallow any future extra fields safely
    ):
        """
        Resolution flow:
        1) Validate route context
        2) Load CountryProfile (if profile_id exists)
        3) Cache
        4) AI answer (always allowed if route exists)
        """

        question_clean = (question or "").strip()
        visa_type_clean = (visa_type or "").strip()

        # 0) No route context → user must select route
        if not profile_id and not (source_country and destination_country):
            return {
                "response": "Please select your citizenship and destination first so I can guide you accurately.",
                "source": "system",
                "cached": False,
                "visa_type": visa_type_clean or None,
            }

        # 1) Load CountryProfile if available
        profile = None
        if profile_id:
            profile = (
                db.query(CountryProfile)
                .filter(CountryProfile.profile_id == profile_id)
                .first()
            )

        # 2) Cache key includes route + user context
        cache_key_raw = f"{question_clean}|{visa_type_clean}|{profile_id}|{source_country}|{residence_country}|{destination_country}|{employment_status}"
        cache_key = hashlib.sha256(cache_key_raw.encode("utf-8")).hexdigest()

        cached_value = cache.get(cache_key)
        if cached_value:
            return {
                "response": cached_value,
                "source": "cache",
                "cached": True,
                "visa_type": visa_type_clean or None,
            }

        # 3) Build AI grounding context
        context = self._build_context(
            profile=profile,
            source_country=source_country,
            residence_country=residence_country,
            destination_country=destination_country,
            visa_type=visa_type_clean,
            employment_status=employment_status,
        )

        # 4) Ask AI
        ai_response = self._ask_ai(question_clean, context)

        # 5) Cache it
        cache.set(cache_key, ai_response)

        return {
            "response": ai_response,
            "source": "ai",
            "cached": False,
            "visa_type": visa_type_clean or None,
        }

    def _build_context(
        self,
        profile: Optional[CountryProfile],
        source_country: Optional[str],
        residence_country: Optional[str],
        destination_country: Optional[str],
        visa_type: Optional[str],
        employment_status: Optional[str],
    ) -> str:
        """
        Grounding rules:
        - If profile exists: treat it as authoritative on requirements.
        - If profile missing: allow procedural help but don't invent requirements.
        """

        if not profile:
            return f"""
You are a visa assistant.

Known route:
- Citizenship: {source_country or "Not provided"}
- Current residence: {residence_country or "Not provided"}
- Destination: {destination_country or "Not provided"}
- Visa type: {visa_type or "Not provided"}
- Employment status: {employment_status or "Not provided"}

Rules:
- Explain application steps and forms clearly (e.g., DS-160 process)
- Do NOT invent required documents
- If unsure about a requirement, say so
- Always advise verifying with official government sources
"""

        # ✅ These are the correct fields based on your loader/profile_matcher:
        requirements: Dict[str, Any] = profile.requirements or {}
        mandatory = requirements.get("mandatory_documents", [])
        recommended = requirements.get("strongly_recommended", [])
        not_required = requirements.get("not_required", [])

        interview_details = getattr(profile, "interview_details", None)
        timeline = getattr(profile, "timeline", None)

        return f"""
You are a visa assistant.

Verified route (authoritative profile):
- Citizenship: {profile.source_country}
- Current residence: {getattr(profile, "residence_country", profile.source_country)}
- Destination: {profile.destination_country}
- Visa: {profile.visa_name} ({profile.visa_type})
- Employment status: {getattr(profile, "employment_status", "Not provided")}

Verified requirements (authoritative):
Mandatory documents:
{mandatory}

Recommended documents:
{recommended}

Not required:
{not_required}

Interview details:
{interview_details}

Timeline:
{timeline}

Rules:
- Requirements above are authoritative
- You MAY explain application steps, forms (e.g., DS-160), interview flow, and timelines
- Do NOT invent new required documents
- Be clear, structured, and practical
- Always advise verifying with official government sources
"""

    def _ask_ai(self, question: str, context: str) -> str:
        prompt = f"""{context}

User question:
{question}

Answer clearly and step-by-step where applicable.
"""
        response = self.model.generate_content(prompt)
        return (getattr(response, "text", "") or "").strip()


# ✅ exported singleton used by main.py
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
ai_engine = AIEngine(_model)
