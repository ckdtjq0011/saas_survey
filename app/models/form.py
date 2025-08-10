from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class QuestionType(str, enum.Enum):
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    MULTIPLE_CHOICE = "multiple_choice"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    SCALE = "scale"
    DATE = "date"
    TIME = "time"
    FILE_UPLOAD = "file_upload"
    EMAIL = "email"
    NUMBER = "number"


class Form(Base):
    __tablename__ = "forms"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    accepts_responses = Column(Boolean, default=True)
    requires_login = Column(Boolean, default=False)
    
    # New fields
    share_token = Column(String, unique=True, index=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    max_responses = Column(Integer, nullable=True)
    
    # Settings
    limit_one_response = Column(Boolean, default=False)
    show_progress_bar = Column(Boolean, default=False)
    shuffle_questions = Column(Boolean, default=False)
    confirmation_message = Column(Text, default="Thank you for your response!")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", backref="forms")
    questions = relationship("Question", back_populates="form", cascade="all, delete-orphan", order_by="Question.order")
    responses = relationship("FormResponse", back_populates="form", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    required = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    # Options for multiple choice, checkbox, dropdown
    options = Column(JSON)  # List of options
    
    # Settings for specific question types
    settings = Column(JSON)  # e.g., min/max for scale, date range, file types, etc.
    
    # Validation
    validation_rules = Column(JSON)  # Custom validation rules
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    form = relationship("Form", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class FormResponse(Base):
    __tablename__ = "form_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"), nullable=False)
    respondent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    respondent_email = Column(String)
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Relationships
    form = relationship("Form", back_populates="responses")
    respondent = relationship("User", backref="form_responses")
    answers = relationship("Answer", back_populates="response", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("form_responses.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    
    # Store different types of answers
    text_answer = Column(Text)
    number_answer = Column(Integer)
    json_answer = Column(JSON)  # For multiple choice, checkbox selections
    file_url = Column(String)  # For file uploads
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    response = relationship("FormResponse", back_populates="answers")
    question = relationship("Question", back_populates="answers")