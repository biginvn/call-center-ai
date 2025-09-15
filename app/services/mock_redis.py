"""
Mock Redis service để test khi chưa có Redis server
"""
import json
from typing import Dict, Optional, Any

class MockRedis:
    def __init__(self):
        self.data: Dict[str, str] = {}
    
    def set(self, key: str, value: str) -> bool:
        self.data[key] = value
        return True
    
    def get(self, key: str) -> Optional[str]:
        return self.data.get(key)
    
    def delete(self, key: str) -> bool:
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def keys(self, pattern: str = "*") -> list:
        if pattern == "*":
            return list(self.data.keys())
        # Simple pattern matching
        import fnmatch
        return [key for key in self.data.keys() if fnmatch.fnmatch(key, pattern)]

# Global mock redis instance
mock_redis = MockRedis()
