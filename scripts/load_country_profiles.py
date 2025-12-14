# Create profile loader script
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, CountryProfile
from sqlalchemy import text

def load_profiles():
    """Load country profiles from JSON into database"""
    
    # Read JSON file
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data',
        'verified_country_profiles.json'
    )
    
    print(f"Loading from: {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    db = SessionLocal()
    
    try:
        # Clear existing profiles
        db.execute(text("DELETE FROM country_profiles"))
        db.commit()
        print("Cleared existing profiles")
        
        # Load new profiles
        for profile in data['profiles']:
            if not profile.get('enabled', True):
                print(f"Skipping disabled profile: {profile['id']}")
                continue
            
            db_profile = CountryProfile(
                profile_id=profile['id'],
                source_country=profile['profile_metadata']['source_country'],
                source_country_code=profile['profile_metadata']['source_country_code'],
                residence_country=profile['profile_metadata']['residence_country'],
                destination_country=profile['profile_metadata']['destination_country'],
                destination_code=profile['profile_metadata']['destination_code'],
                visa_type=profile['profile_metadata']['visa_type'],
                visa_name=profile['profile_metadata']['visa_name'],
                employment_status=profile['profile_metadata'].get('employment_status'),
                requirements=profile['requirements'],
                interview_details=profile.get('interview', {}),
                success_factors=profile.get('success_factors', []),
                rejection_reasons=profile.get('rejection_reasons', []),
                country_specific_tips=profile.get('india_specific_tips', []),
                timeline=profile.get('timeline', {}),
                quick_facts=profile.get('quick_facts', {}),
                verification_status=profile['profile_metadata'].get('verification_status'),
                last_verified=profile['profile_metadata'].get('last_verified')
            )
            
            db.add(db_profile)
            print(f"Added profile: {profile['id']}")
        
        db.commit()
        print(f"\n✅ Successfully loaded {len(data['profiles'])} profiles")
        
        # Verify
        count = db.execute(text("SELECT COUNT(*) FROM country_profiles")).scalar()
        print(f"✅ Verified: {count} profiles in database")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_profiles()