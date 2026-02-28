from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import os

Base = declarative_base()


class EquipmentList(Base):
    __tablename__ = 'equipment_list'
    
    id = Column(Integer, primary_key=True)
    location = Column(String(50))
    category = Column(String(50))
    item_name = Column(String(100))
    model_name = Column(String(100))
    specs = Column(Text)
    image_path = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    
    votes = relationship("IndividualVote", back_populates="equipment", cascade="all, delete-orphan")


class UserPolicySurvey(Base):
    __tablename__ = 'user_policy_survey'
    
    phone_suffix = Column(String(4), primary_key=True)
    policy_choice = Column(String(50))
    additional_requests = Column(Text)
    submitted_at = Column(DateTime, default=func.now())
    
    votes = relationship("IndividualVote", back_populates="user", cascade="all, delete-orphan")


class IndividualVote(Base):
    __tablename__ = 'individual_votes'
    
    id = Column(Integer, primary_key=True)
    phone_suffix = Column(String(4), ForeignKey('user_policy_survey.phone_suffix', ondelete='CASCADE'))
    equipment_id = Column(Integer, ForeignKey('equipment_list.id', ondelete='CASCADE'))
    vote_type = Column(String(50))
    
    user = relationship("UserPolicySurvey", back_populates="votes")
    equipment = relationship("EquipmentList", back_populates="votes")


def get_engine():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return create_engine(db_url)


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
