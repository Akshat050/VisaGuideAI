import redis
import json
import hashlib
from typing import Optional, Any
import os
from dotenv import load_dotenv

load_dotenv()

class CacheLayer:
    def __init__(self):
        try:
            self.redis = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)
            self.redis.ping()
            print("✅ Redis connected")
        except:
            print("⚠️  Redis not available")
            self.redis = None
    
    def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.redis:
            return False
        try:
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except:
            return False
    
    def hash_question(self, question: str, visa_type: str) -> str:
        return hashlib.md5(f"{visa_type}:{question.lower()}".encode()).hexdigest()

cache = CacheLayer()
