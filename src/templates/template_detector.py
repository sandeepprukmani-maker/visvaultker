import json
import hashlib
import os
from typing import Dict, List, Optional
from difflib import SequenceMatcher

class TemplateDetector:
    def __init__(self, templates_path: str = "./data/templates.json"):
        self.templates_path = templates_path
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        if os.path.exists(self.templates_path):
            with open(self.templates_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_templates(self):
        os.makedirs(os.path.dirname(self.templates_path), exist_ok=True)
        with open(self.templates_path, 'w') as f:
            json.dump(self.templates, f, indent=2)
    
    def normalize_structure(self, dom_structure: Dict) -> str:
        def normalize_node(node):
            if not isinstance(node, dict):
                return ''
            
            tag = node.get('tag', '')
            id_val = node.get('id', '')
            classes = node.get('classes', '')
            role = node.get('role', '')
            children = node.get('children', [])
            
            normalized = f"{tag}"
            if id_val:
                normalized += f"#{id_val}"
            if classes:
                normalized += f".{classes.split()[0]}"
            if role:
                normalized += f"[role={role}]"
            
            if children:
                child_structures = [normalize_node(child) for child in children]
                normalized += "{" + ",".join(child_structures) + "}"
            
            return normalized
        
        return normalize_node(dom_structure)
    
    def calculate_similarity(self, structure1: str, structure2: str) -> float:
        return SequenceMatcher(None, structure1, structure2).ratio()
    
    def detect_template(self, dom_structure: Dict, url: str = "") -> str:
        normalized = self.normalize_structure(dom_structure)
        structure_hash = hashlib.sha256(normalized.encode()).hexdigest()
        
        for template_id, template_data in self.templates.items():
            stored_normalized = template_data.get('normalized_structure', '')
            similarity = self.calculate_similarity(normalized, stored_normalized)
            
            if similarity >= 0.95:
                template_data['urls'].append(url)
                template_data['match_count'] += 1
                self._save_templates()
                return template_id
        
        template_id = f"template_{structure_hash[:12]}"
        self.templates[template_id] = {
            "template_id": template_id,
            "structure_hash": structure_hash,
            "normalized_structure": normalized,
            "urls": [url],
            "match_count": 1,
            "dom_structure": dom_structure
        }
        self._save_templates()
        
        return template_id
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> Dict:
        return self.templates
    
    def get_unique_template_count(self) -> int:
        return len(self.templates)
