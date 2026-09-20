from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String, unique=True, index=True, nullable=False)
    subject = Column(String)
    sender = Column(String)
    date = Column(String)
    snippet = Column(Text)
    body = Column(Text)