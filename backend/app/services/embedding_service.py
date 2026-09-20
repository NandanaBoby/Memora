from sentence_transformers import SentenceTransformer
from app.database import SessionLocal
from app.models.email import Email
from app.models.chunk import Chunk

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def chunk_text(text, max_words=200, overlap_words=30):
    """Simple word-based chunking with overlap. Good enough for short emails."""
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [text.strip()]

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunk = ' '.join(words[start:end])
        chunks.append(chunk.strip())
        start += max_words - overlap_words
    return chunks


def embed_and_store_emails():
    model = get_model()
    db = SessionLocal()

    emails = db.query(Email).all()
    total_chunks = 0

    for email in emails:
        # Skip if this email's chunks already exist
        existing = db.query(Chunk).filter(Chunk.email_id == email.id).first()
        if existing:
            continue

        # Use body if available, fall back to snippet
        source_text = email.body.strip() if email.body and email.body.strip() else email.snippet
        text_to_chunk = f"Subject: {email.subject}\n\n{source_text}"

        pieces = chunk_text(text_to_chunk)
        for piece in pieces:
            embedding = model.encode(piece).tolist()
            chunk = Chunk(email_id=email.id, text=piece, embedding=embedding)
            db.add(chunk)
            total_chunks += 1

    db.commit()
    db.close()
    print(f"Created {total_chunks} chunks from {len(emails)} emails.")


if __name__ == '__main__':
    embed_and_store_emails()