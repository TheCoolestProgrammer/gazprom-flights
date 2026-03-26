from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from src.database import Base

    
class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(100), nullable=False)
    aircraft_type = Column(String(100), nullable=False)
    
    passengers = relationship("passengers",back_populates='departments')
    passenger_flights = relationship("passenger_flight",back_populates='flights')
