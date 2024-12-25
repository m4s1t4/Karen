from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import VECTOR

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    messages = relationship("Message", back_populates="chat_session")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    chat_session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=True)
    user_id = Column(String, nullable=True)
    role = Column(String, nullable=False)  # "user" o "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    embedding = Column(VECTOR(1536), nullable=True)  # Para embeddings de OpenAI
    
    chat_session = relationship("ChatSession", back_populates="messages")

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    github_url = Column(String, nullable=True)
    user_id = Column(String, nullable=True)

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    embedding = Column(VECTOR(1536), nullable=True)  # Para búsqueda semántica
    
    project = relationship("Project", backref="files") 