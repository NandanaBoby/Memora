from fastapi import APIRouter
from sqlalchemy import select
from app.database import SessionLocal
from app.models.chunk import Chunk
from app.models.email import Email
from app.services.embedding_service import get_model

router = APIRouter()


@router.get("/search")
def search(q: str, top_k: int = 5):
    model = get_model()
    query_embedding = model.encode(q).tolist()

    db = SessionLocal()
    results = (
        db.query(Chunk, Email)
        .join(Email, Chunk.email_id == Email.id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
    db.close()

    return [
        {
            "chunk_text": chunk.text,
            "email_subject": email.subject,
            "email_sender": email.sender,
            "email_date": email.date,
            "chunk_id": chunk.id,
        }
        for chunk, email in results
    ]