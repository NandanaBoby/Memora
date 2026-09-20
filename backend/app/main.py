from fastapi import FastAPI
from app.routers import search

app = FastAPI(title="Memora AI Backend")

app.include_router(search.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}