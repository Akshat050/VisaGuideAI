import sys
sys.path.append('/Users/akshu/Project/VisaGuideAI/backend')
from app.database import SessionLocal, VisaRequirement, VisaQA
import json
from datetime import date

db = SessionLocal()
with open('/Users/akshu/Project/VisaGuideAI/data/us_b1b2_visa.json') as f:
    data = json.load(f)

print("📁 Loading visa data...")

# Add visa requirement
visa_req = VisaRequirement(
    visa_type='us_b1b2',
    source_country=data['visa_info']['source_country'],
    target_country=data['visa_info']['target_country'],
    requirements=data,
    official_source_url=data['visa_info']['official_source'],
    last_verified_date=date.today(),
    last_verified_by='Initial Load'
)
db.add(visa_req)

# Add Q&A
for qa in data['common_questions']:
    qa_entry = VisaQA(
        visa_type='us_b1b2',
        question=qa['question'],
        answer=qa['detailed_answer'],
        category=qa['category'],
        source='Official docs',
        verified_date=date.today()
    )
    db.add(qa_entry)

db.commit()
print(f"✅ Loaded {len(data['required_documents'])} docs, {len(data['common_questions'])} Q&A")
db.close()