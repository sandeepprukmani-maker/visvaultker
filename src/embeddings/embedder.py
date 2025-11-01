import chromadb
from chromadb.config import Settings
from openai import OpenAI
from typing import List, Dict, Optional
import json

class ElementEmbedder:
    def __init__(self, openai_api_key: str, db_path: str = "./data/vector_db", cache=None):
        self.client = OpenAI(api_key=openai_api_key)
        self.chroma_client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="ui_elements",
            metadata={"hnsw:space": "cosine"}
        )
        self.cache = cache
    
    def generate_embedding(self, text: str) -> List[float]:
        if self.cache:
            cached = self.cache.get(text)
            if cached:
                return cached
        
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding = response.data[0].embedding
        
        if self.cache:
            self.cache.set(text, embedding)
        
        return embedding
    
    def create_element_description(self, element: Dict) -> str:
        parts = []
        
        if element.get('tag'):
            parts.append(f"{element['tag']} element")
        
        if element.get('role'):
            parts.append(f"with role '{element['role']}'")
        
        if element.get('ariaLabel'):
            parts.append(f"labeled '{element['ariaLabel']}'")
        
        if element.get('placeholder'):
            parts.append(f"placeholder '{element['placeholder']}'")
        
        if element.get('text'):
            parts.append(f"containing text '{element['text'][:50]}'")
        
        if element.get('type'):
            parts.append(f"of type '{element['type']}'")
        
        if element.get('name'):
            parts.append(f"named '{element['name']}'")
        
        if element.get('id'):
            parts.append(f"with id '{element['id']}'")
        
        if element.get('classes'):
            parts.append(f"with classes '{element['classes']}'")
        
        return " ".join(parts)
    
    def index_element(self, template_id: str, element: Dict, url: str):
        description = self.create_element_description(element)
        
        if not description.strip():
            return
        
        embedding = self.generate_embedding(description)
        
        element_id = f"{template_id}_{element.get('selector', '').replace(' ', '_')[:50]}"
        
        metadata = {
            "template_id": template_id,
            "url": url,
            "tag": element.get('tag', ''),
            "selector": element.get('selector', ''),
            "is_interactive": str(element.get('isInteractive', False)),
            "element_json": json.dumps(element)
        }
        
        self.collection.upsert(
            ids=[element_id],
            embeddings=[embedding],
            documents=[description],
            metadatas=[metadata]
        )
    
    def index_page_elements(self, template_id: str, elements: List[Dict], url: str):
        for element in elements:
            try:
                self.index_element(template_id, element, url)
            except Exception as e:
                print(f"Error indexing element: {e}")
    
    def search_similar_elements(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self.generate_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        matched_elements = []
        if results and results.get('ids') and results.get('metadatas') and results.get('documents') and results.get('distances'):
            ids = results['ids'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0]
            distances = results['distances'][0]
            
            if ids and metadatas and documents and distances:
                for i, element_id in enumerate(ids):
                    metadata = metadatas[i]
                    element_json_str = metadata.get('element_json', '{}')
                    element_data = json.loads(str(element_json_str))
                    matched_elements.append({
                        "element_id": element_id,
                        "description": documents[i],
                        "similarity": 1 - distances[i],
                        "template_id": metadata.get('template_id', ''),
                        "url": metadata.get('url', ''),
                        "selector": metadata.get('selector', ''),
                        "element": element_data
                    })
        
        return matched_elements
