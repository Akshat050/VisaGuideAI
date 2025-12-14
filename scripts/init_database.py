import sys
sys.path.append('/Users/akshu/Project/VisaGuideAI/backend')
from app.database import init_db

if __name__ == "__main__":
    init_db()