"""
Database setup.
Week 3: Store PR reviews in SQLite using SQLAlchemy.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./reviews.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    diff_url = Column(String, nullable=False)
    review_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def save_review(
    repo_name: str,
    pr_number: int,
    pr_title: str,
    author: str,
    diff_url: str,
    review_text: str,
) -> Review:
    db = SessionLocal()
    try:
        review = Review(
            repo_name=repo_name,
            pr_number=pr_number,
            pr_title=pr_title,
            author=author,
            diff_url=diff_url,
            review_text=review_text,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        print(f"[database] Review saved for PR #{pr_number}")
        return review
    finally:
        db.close()


def get_all_reviews() -> list:
    db = SessionLocal()
    try:
        return db.query(Review).order_by(Review.created_at.desc()).all()
    finally:
        db.close()