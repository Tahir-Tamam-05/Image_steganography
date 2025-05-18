import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create database directory if it doesn't exist
os.makedirs('data/database', exist_ok=True)

# Create SQLite database engine
DATABASE_URL = "sqlite:///data/database/steganography.db"
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

# Define Image model
class StegImage(Base):
    __tablename__ = "steg_images"
    
    id = Column(Integer, primary_key=True)
    original_filename = Column(String(255), nullable=False)
    encoded_filename = Column(String(255), nullable=False)
    original_path = Column(String(255))
    encoded_path = Column(String(255), nullable=False)
    message_length = Column(Integer, nullable=False)
    message_preview = Column(String(50))  # First 50 chars of message
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    image_width = Column(Integer)
    image_height = Column(Integer)
    file_size_kb = Column(Float)
    capacity_chars = Column(Integer)
    is_successful = Column(Boolean, default=True)
    notes = Column(Text)
    
    def __repr__(self):
        return f"<StegImage {self.id}: {self.encoded_filename}>"

# Create tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Functions to interact with the database
def add_encoded_image(original_filename, encoded_filename, encoded_path, message, 
                     image_width=None, image_height=None, file_size_kb=None, 
                     capacity_chars=None, original_path=None, is_successful=True, notes=None):
    """Add a record of an encoded image to the database"""
    db = SessionLocal()
    try:
        # Create preview of message (first 50 chars)
        if message and len(message) > 50:
            message_preview = message[:47] + "..."
        else:
            message_preview = message
        
        steg_image = StegImage(
            original_filename=original_filename,
            encoded_filename=encoded_filename,
            original_path=original_path,
            encoded_path=encoded_path,
            message_length=len(message) if message else 0,
            message_preview=message_preview,
            image_width=image_width,
            image_height=image_height,
            file_size_kb=file_size_kb,
            capacity_chars=capacity_chars,
            is_successful=is_successful,
            notes=notes
        )
        db.add(steg_image)
        db.commit()
        db.refresh(steg_image)
        return steg_image
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_recent_images(limit=10):
    """Get the most recent encoded images"""
    db = SessionLocal()
    try:
        return db.query(StegImage).order_by(StegImage.created_at.desc()).limit(limit).all()
    finally:
        db.close()

def get_image_by_id(image_id):
    """Get an encoded image by its ID"""
    db = SessionLocal()
    try:
        return db.query(StegImage).filter(StegImage.id == image_id).first()
    finally:
        db.close()

def search_images(search_term):
    """Search for encoded images by filename or message preview"""
    db = SessionLocal()
    try:
        return db.query(StegImage).filter(
            (StegImage.original_filename.like(f"%{search_term}%")) |
            (StegImage.encoded_filename.like(f"%{search_term}%")) |
            (StegImage.message_preview.like(f"%{search_term}%"))
        ).order_by(StegImage.created_at.desc()).all()
    finally:
        db.close()

def delete_image_record(image_id):
    """Delete a record from the database (not the actual file)"""
    db = SessionLocal()
    try:
        image = db.query(StegImage).filter(StegImage.id == image_id).first()
        if image:
            db.delete(image)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_stats():
    """Get statistics about encoded images"""
    db = SessionLocal()
    try:
        total_images = db.query(StegImage).count()
        successful_encodings = db.query(StegImage).filter(StegImage.is_successful == True).count()
        
        # Get total message chars encoded
        result = db.query(StegImage).with_entities(
            StegImage.message_length,
        ).all()
        total_message_chars = sum(r.message_length for r in result)
        
        return {
            "total_images": total_images,
            "successful_encodings": successful_encodings,
            "total_message_chars": total_message_chars
        }
    finally:
        db.close()