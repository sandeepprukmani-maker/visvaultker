from typing import Dict, Optional, List
from src.embeddings.embedder import ElementEmbedder
from src.executor.vision_finder import VisionFinder
from playwright.async_api import Page

class SelfHealer:
    def __init__(self, embedder: ElementEmbedder, enable_vision: bool = True, vision_threshold: float = 0.75):
        self.embedder = embedder
        self.enable_vision = enable_vision
        self.vision_finder = VisionFinder(vision_threshold=vision_threshold) if enable_vision else None
    
    async def heal_broken_locator(
        self, 
        old_description: str, 
        page: Page,
        confidence_threshold: float = 0.8,
        enable_vision: Optional[bool] = None,
        vision_threshold: Optional[float] = None
    ) -> Optional[Dict]:
        if enable_vision is None:
            enable_vision = self.enable_vision
        if vision_threshold is None and self.vision_finder:
            vision_threshold = self.vision_finder.vision_threshold
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
                                "method": "semantic_dom",
                                "original_description": old_description
                            }
        
        if enable_vision and self.vision_finder and vision_threshold and (not best_match or best_confidence < vision_threshold):
            print(f"🎯 DOM confidence {best_confidence:.2f} below threshold {vision_threshold:.2f}, trying vision fallback...")
            vision_result = await self.vision_finder.find_element_with_vision(
                page=page,
                description=old_description,
                context="Self-healing broken selector"
            )
            
            if vision_result and vision_result.get('confidence', 0) > best_confidence:
                print(f"✅ Vision found better match: confidence {vision_result['confidence']:.2f}")
                best_match = vision_result
                best_match['original_description'] = old_description
        
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
