from typing import Dict, Optional, List
from src.embeddings.embedder import ElementEmbedder
from playwright.async_api import Page

class SelfHealer:
    def __init__(self, embedder: ElementEmbedder):
        self.embedder = embedder
    
    async def heal_broken_locator(
        self, 
        old_description: str, 
        page: Page,
        confidence_threshold: float = 0.8
    ) -> Optional[Dict]:
        current_elements = await page.evaluate('''() => {
            function extractElements(element, path = '') {
                const elements = [];
                if (element.nodeType !== 1) return elements;
                
                const tag = element.tagName.toLowerCase();
                const id = element.id || '';
                const classes = Array.from(element.classList).join(' ');
                const text = element.textContent?.trim().substring(0, 100) || '';
                const role = element.getAttribute('role') || '';
                const ariaLabel = element.getAttribute('aria-label') || '';
                
                const currentPath = path + ' > ' + tag + (id ? '#' + id : '');
                
                elements.push({
                    tag, id, classes, text, role, ariaLabel,
                    selector: currentPath
                });
                
                for (let child of element.children) {
                    elements.push(...extractElements(child, currentPath));
                }
                
                return elements;
            }
            return extractElements(document.body);
        }''')
        
        similar_elements = self.embedder.search_similar_elements(old_description, top_k=5)
        
        best_match = None
        best_confidence = 0
        
        for similar in similar_elements:
            if similar['similarity'] >= confidence_threshold:
                for current_element in current_elements:
                    if self._elements_match(similar['element'], current_element):
                        if similar['similarity'] > best_confidence:
                            best_confidence = similar['similarity']
                            best_match = {
                                "selector": current_element['selector'],
                                "confidence": similar['similarity'],
                                "element": current_element,
                                "healing_applied": True,
                                "original_description": old_description
                            }
        
        return best_match
    
    def _elements_match(self, stored_element: Dict, current_element: Dict) -> bool:
        if stored_element.get('id') and stored_element['id'] == current_element.get('id'):
            return True
        
        if stored_element.get('tag') != current_element.get('tag'):
            return False
        
        stored_classes = set(stored_element.get('classes', '').split())
        current_classes = set(current_element.get('classes', '').split())
        class_overlap = len(stored_classes & current_classes) / max(len(stored_classes), len(current_classes), 1)
        
        if class_overlap > 0.7:
            return True
        
        if stored_element.get('ariaLabel') and stored_element['ariaLabel'] == current_element.get('ariaLabel'):
            return True
        
        return False
