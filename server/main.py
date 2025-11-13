from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import numpy as np

from server.database import get_db, init_db
from server.models import AutomationHistory

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if not a or not b or len(a) != len(b):
        return 0.0
    
    a_np = np.array(a)
    b_np = np.array(b)
    
    dot_product = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return float(dot_product / (norm_a * norm_b))

app = FastAPI(title="VisionVault API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AutomationRequest(BaseModel):
    prompt: str
    detected_url: Optional[str] = None
    mode: str
    model: str
    success: bool
    session_id: str
    logs: list
    generated_code: dict
    screenshot: Optional[str] = None
    error: Optional[str] = None
    prompt_embedding: Optional[list] = None

class AutomationResponse(BaseModel):
    id: int
    prompt: str
    detectedUrl: Optional[str]
    mode: str
    model: str
    success: bool
    sessionId: str
    logs: list
    generatedCode: dict
    screenshot: Optional[str]
    error: Optional[str]
    createdAt: str

    class Config:
        from_attributes = True

@app.on_event("startup")
async def startup():
    init_db()
    print("Database initialized")

@app.get("/")
async def root():
    return {"message": "VisionVault API", "status": "running"}

@app.get("/api/history")
async def get_history(db: Session = Depends(get_db)):
    history = db.query(AutomationHistory).order_by(AutomationHistory.created_at.desc()).all()
    return [h.to_dict() for h in history]

@app.get("/api/history/{id}")
async def get_history_by_id(id: int, db: Session = Depends(get_db)):
    history = db.query(AutomationHistory).filter(AutomationHistory.id == id).first()
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    
    return history.to_dict()

@app.post("/api/history")
async def create_history(request: AutomationRequest, db: Session = Depends(get_db)):
    history = AutomationHistory(
        prompt=request.prompt,
        prompt_embedding=request.prompt_embedding,
        detected_url=request.detected_url,
        mode=request.mode,
        model=request.model,
        success=request.success,
        session_id=request.session_id,
        logs=request.logs,
        generated_code=request.generated_code,
        screenshot=request.screenshot,
        error=request.error
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return {"id": history.id, "message": "History saved successfully"}

@app.delete("/api/history/{id}")
async def delete_history(id: int, db: Session = Depends(get_db)):
    history = db.query(AutomationHistory).filter(AutomationHistory.id == id).first()
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    
    db.delete(history)
    db.commit()
    
    return {"message": "History deleted successfully"}

@app.delete("/api/history")
async def delete_all_history(db: Session = Depends(get_db)):
    db.query(AutomationHistory).delete()
    db.commit()
    
    return {"message": "All history deleted successfully"}

@app.get("/api/cache")
async def get_cache(db: Session = Depends(get_db)):
    cached = db.query(AutomationHistory).filter(
        AutomationHistory.prompt_embedding.isnot(None)
    ).order_by(AutomationHistory.created_at.desc()).all()
    
    return [h.to_dict() for h in cached]

class SimilarityRequest(BaseModel):
    embedding: List[float]
    threshold: float = 0.85
    limit: int = 10

@app.post("/api/similarity-search")
async def similarity_search(request: SimilarityRequest, db: Session = Depends(get_db)):
    """Find similar automations based on embedding cosine similarity"""
    all_history = db.query(AutomationHistory).filter(
        AutomationHistory.prompt_embedding.isnot(None)
    ).all()
    
    results = []
    for h in all_history:
        if h.prompt_embedding:
            similarity = cosine_similarity(request.embedding, h.prompt_embedding)
            if similarity >= request.threshold:
                result = h.to_dict()
                result['similarity'] = similarity
                results.append(result)
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:request.limit]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
