from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from app.database import CountryProfile

class ProfileMatcher:
    """Match user profile to appropriate visa requirements"""
    
    def get_available_countries(self, db: Session) -> Dict[str, List[str]]:
        """Get all available source and destination countries"""
        profiles = db.query(CountryProfile).filter(CountryProfile.enabled == True).all()
        
        source_countries = {}
        destination_countries = set()
        
        for profile in profiles:
            source = profile.source_country
            dest = profile.destination_country
            
            if source not in source_countries:
                source_countries[source] = []
            
            if dest not in source_countries[source]:
                source_countries[source].append(dest)
            
            destination_countries.add(dest)
        
        return {
            "source_countries": list(source_countries.keys()),
            "destination_countries": list(destination_countries),
            "routes": source_countries
        }
    
    def find_matching_profile(
        self,
        db: Session,
        source_country: str,
        residence_country: Optional[str],
        destination_country: str,
        visa_type: Optional[str] = None,
        employment_status: Optional[str] = None
    ) -> Optional[CountryProfile]:
        """Find the best matching profile for user's situation"""
        
        # Build query
        query = db.query(CountryProfile).filter(
            CountryProfile.enabled == True,
            CountryProfile.source_country == source_country,
            CountryProfile.destination_country == destination_country
        )
        
        # Use residence country if different from source
        if residence_country and residence_country != source_country:
            query = query.filter(CountryProfile.residence_country == residence_country)
        else:
            query = query.filter(CountryProfile.residence_country == source_country)
        
        # Filter by visa type if specified
        if visa_type:
            query = query.filter(CountryProfile.visa_type == visa_type)
        
        # Filter by employment status if specified
        if employment_status:
            query = query.filter(CountryProfile.employment_status == employment_status)
        
        # Get first match (can be enhanced to rank matches)
        profile = query.first()
        
        # If no exact match, try without employment status
        if not profile and employment_status:
            query = db.query(CountryProfile).filter(
                CountryProfile.enabled == True,
                CountryProfile.source_country == source_country,
                CountryProfile.destination_country == destination_country
            )
            profile = query.first()
        
        return profile
    
    def get_personalized_requirements(
        self,
        db: Session,
        source_country: str,
        residence_country: Optional[str],
        destination_country: str,
        employment_status: str = "employed"
    ) -> Dict:
        """Get personalized requirements based on user profile"""
        
        profile = self.find_matching_profile(
            db=db,
            source_country=source_country,
            residence_country=residence_country or source_country,
            destination_country=destination_country,
            employment_status=employment_status
        )
        
        if not profile:
            return {
                "found": False,
                "message": f"No visa requirements found for {source_country} → {destination_country}",
                "available_routes": self.get_available_countries(db)["routes"]
            }
        
        # Extract and format requirements
        return {
            "found": True,
            "profile_id": profile.profile_id,
            "route": {
                "from": profile.source_country,
                "to": profile.destination_country,
                "visa_type": profile.visa_type,
                "visa_name": profile.visa_name
            },
            "quick_facts": profile.quick_facts,
            "requirements": {
                "mandatory": profile.requirements.get("mandatory_documents", []),
                "recommended": profile.requirements.get("strongly_recommended", []),
                "not_required": profile.requirements.get("not_required", [])
            },
            "interview": profile.interview_details,
            "success_factors": profile.success_factors,
            "common_rejections": profile.rejection_reasons,
            "country_specific_tips": profile.country_specific_tips,
            "timeline": profile.timeline,
            "verification_status": profile.verification_status
        }
    
    def compare_profiles(
        self,
        db: Session,
        profile_ids: List[str]
    ) -> Dict:
        """Compare multiple profiles side by side"""
        
        profiles = db.query(CountryProfile).filter(
            CountryProfile.profile_id.in_(profile_ids)
        ).all()
        
        comparison = []
        for profile in profiles:
            comparison.append({
                "route": f"{profile.source_country} → {profile.destination_country}",
                "visa_fee": profile.quick_facts.get("visa_fee_usd"),
                "processing_days": profile.quick_facts.get("processing_days"),
                "interview_required": profile.quick_facts.get("interview_required"),
                "mandatory_docs_count": len(profile.requirements.get("mandatory_documents", [])),
                "unique_requirements": self._get_unique_requirements(profile)
            })
        
        return {"comparison": comparison}
    
    def _get_unique_requirements(self, profile: CountryProfile) -> List[str]:
        """Extract country-specific unique requirements"""
        unique = []
        
        # Check for special documents
        for doc in profile.requirements.get("mandatory_documents", []):
            doc_name = doc.get("name", "").lower()
            if any(term in doc_name for term in ["hukou", "yellow fever", "sponsor", "affidavit"]):
                unique.append(doc.get("name"))
        
        return unique

profile_matcher = ProfileMatcher()
