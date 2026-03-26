from sqlalchemy import Column, Integer, String, BigInteger, Text, ForeignKey, Float, Date, Enum
from sqlalchemy.orm import relationship

import datetime

from src.database import Base

    
import enum

class Gender(enum.Enum):
    MALE="male"
    FEMALE="female"

class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100), nullable=False)
    birthdate = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    passport = Column(BigInteger, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))

    trip_purpose = Column(Text, nullable=False)
    cargo_weight = Column(Float)
    notes = Column(Text)
    request_date = Column(Date, default=datetime.datetime.now)
    fact_date = Column(Date)
    
    departments = relationship("Department", back_populates="passengers")
    passenger_flights = relationship("PassengerFlight",back_populates='passengers')
    def __str__(self):
        return self.fullname