import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    predictions = relationship(
        "Prediction",
        foreign_keys="[Prediction.creator_id]",
        back_populates="creator",
        cascade="all, delete-orphan",
    )


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    predictions = relationship("Prediction", back_populates="category")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    opponent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    confidence = Column(Float)
    status = Column(String, default="PENDING")
    outcome = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    creator = relationship("User", back_populates="predictions", foreign_keys=[creator_id])
    opponent = relationship("User", foreign_keys=[opponent_id])
    category = relationship("Category", back_populates="predictions")
