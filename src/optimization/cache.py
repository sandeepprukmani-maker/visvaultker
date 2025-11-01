import json
import os
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class EmbeddingCache:
    def __init__(self, cache_path: str = "./data/embedding_cache", ttl_hours: int = 168):
        self.cache_path = cache_path
        os.makedirs(cache_path, exist_ok=True)
        self.cache_file = os.path.join(cache_path, "cache.json")
        self.ttl = timedelta(hours=ttl_hours)
        self.cache = self._load_cache()
        self.hits = 0
        self.misses = 0
    
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _get_cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        key = self._get_cache_key(text)
        
        if key in self.cache:
            entry = self.cache[key]
            cached_time = datetime.fromisoformat(entry['timestamp'])
            
            if datetime.now() - cached_time < self.ttl:
                self.hits += 1
                return entry['embedding']
            else:
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, text: str, embedding: List[float]):
        key = self._get_cache_key(text)
        
        self.cache[key] = {
            "text_preview": text[:100],
            "embedding": embedding,
            "timestamp": datetime.now().isoformat()
        }
        
        if len(self.cache) % 100 == 0:
            self._save_cache()
    
    def clear_expired(self):
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            cached_time = datetime.fromisoformat(entry['timestamp'])
            if now - cached_time >= self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    def flush(self):
        self.cache = {}
        self._save_cache()
        self.hits = 0
        self.misses = 0
