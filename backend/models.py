from sqlalchemy import Column, String, Float, DateTime, Integer
from database import Base
import datetime


class User(Base):
    """User table stores user_id and wallet balance"""
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    wallet_balance = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Journey(Base):
    """Journey table tracks active/completed journeys"""
    __tablename__ = "journeys"

    journey_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    status = Column(String, default="ACTIVE")  # ACTIVE or ENDED
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)


class FareLog(Base):
    """FareLog table records all fare deductions for audit trail"""
    __tablename__ = "fare_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    journey_id = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String)
