from fastapi import FastAPI

app = FastAPI(title="Memora AI Backend")

@app.get("/health")
def health_check():
    return {"status": "ok"}