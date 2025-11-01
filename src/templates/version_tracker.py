import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from difflib import unified_diff

class VersionTracker:
    def __init__(self, versions_path: str = "./data/versions"):
        self.versions_path = versions_path
        os.makedirs(versions_path, exist_ok=True)
        self.versions_index_path = os.path.join(versions_path, "versions_index.json")
        self.versions_index = self._load_versions_index()
    
    def _load_versions_index(self) -> Dict:
        if os.path.exists(self.versions_index_path):
            with open(self.versions_index_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_versions_index(self):
        with open(self.versions_index_path, 'w') as f:
            json.dump(self.versions_index, f, indent=2)
    
    def save_crawl_version(self, url: str, crawl_data: Dict) -> str:
        url_safe = url.replace('://', '_').replace('/', '_').replace('?', '_')[:100]
        
        if url not in self.versions_index:
            self.versions_index[url] = {
                "url": url,
                "versions": [],
                "first_crawled": datetime.now().isoformat(),
                "last_crawled": datetime.now().isoformat()
            }
        
        version_id = f"v{len(self.versions_index[url]['versions']) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        version_file = os.path.join(self.versions_path, f"{url_safe}_{version_id}.json")
        
        version_data = {
            "version_id": version_id,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "crawl_data": crawl_data
        }
        
        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
        
        self.versions_index[url]['versions'].append({
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "file": version_file,
            "structure_hash": crawl_data.get('structure_hash', ''),
            "elements_count": len(crawl_data.get('elements', []))
        })
        self.versions_index[url]['last_crawled'] = datetime.now().isoformat()
        
        self._save_versions_index()
        
        return version_id
    
    def get_version(self, url: str, version_id: str) -> Optional[Dict]:
        if url not in self.versions_index:
            return None
        
        for version in self.versions_index[url]['versions']:
            if version['version_id'] == version_id:
                with open(version['file'], 'r') as f:
                    return json.load(f)
        
        return None
    
    def get_latest_version(self, url: str) -> Optional[Dict]:
        if url not in self.versions_index or not self.versions_index[url]['versions']:
            return None
        
        latest = self.versions_index[url]['versions'][-1]
        with open(latest['file'], 'r') as f:
            return json.load(f)
    
    def compare_versions(self, url: str, version_id_1: str, version_id_2: str) -> Dict:
        v1 = self.get_version(url, version_id_1)
        v2 = self.get_version(url, version_id_2)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        changes = {
            "url": url,
            "version_1": version_id_1,
            "version_2": version_id_2,
            "timestamp_1": v1['timestamp'],
            "timestamp_2": v2['timestamp'],
            "structure_changed": v1['crawl_data']['structure_hash'] != v2['crawl_data']['structure_hash'],
            "elements_added": [],
            "elements_removed": [],
            "elements_modified": []
        }
        
        v1_elements = {self._element_key(el): el for el in v1['crawl_data'].get('elements', [])}
        v2_elements = {self._element_key(el): el for el in v2['crawl_data'].get('elements', [])}
        
        v1_keys = set(v1_elements.keys())
        v2_keys = set(v2_elements.keys())
        
        added_keys = v2_keys - v1_keys
        removed_keys = v1_keys - v2_keys
        common_keys = v1_keys & v2_keys
        
        for key in added_keys:
            changes['elements_added'].append(v2_elements[key])
        
        for key in removed_keys:
            changes['elements_removed'].append(v1_elements[key])
        
        for key in common_keys:
            if self._elements_differ(v1_elements[key], v2_elements[key]):
                changes['elements_modified'].append({
                    "old": v1_elements[key],
                    "new": v2_elements[key]
                })
        
        changes['summary'] = {
            "total_added": len(changes['elements_added']),
            "total_removed": len(changes['elements_removed']),
            "total_modified": len(changes['elements_modified']),
            "total_unchanged": len(common_keys) - len(changes['elements_modified'])
        }
        
        return changes
    
    def _element_key(self, element: Dict) -> str:
        tag = element.get('tag', '')
        id_val = element.get('id', '')
        classes = element.get('classes', '')
        selector = element.get('selector', '')
        
        if id_val:
            return f"{tag}#{id_val}"
        if selector:
            return selector
        return f"{tag}.{classes}"
    
    def _elements_differ(self, el1: Dict, el2: Dict) -> bool:
        comparable_fields = ['text', 'ariaLabel', 'placeholder', 'type', 'href', 'role']
        for field in comparable_fields:
            if el1.get(field) != el2.get(field):
                return True
        return False
    
    def get_version_history(self, url: str) -> List[Dict]:
        if url not in self.versions_index:
            return []
        
        return self.versions_index[url]['versions']
    
    def get_all_tracked_urls(self) -> List[str]:
        return list(self.versions_index.keys())
