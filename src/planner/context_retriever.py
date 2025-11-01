from typing import List, Dict
from src.embeddings.embedder import ElementEmbedder

class ContextRetriever:
    def __init__(self, embedder: ElementEmbedder):
        self.embedder = embedder
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict]:
        results = self.embedder.search_similar_elements(query, top_k=top_k)
        
        context_items = []
        for result in results:
            context_items.append({
                "selector": result['selector'],
                "description": result['description'],
                "similarity": result['similarity'],
                "element": result['element'],
                "template_id": result['template_id'],
                "url": result['url']
            })
        
        return context_items
