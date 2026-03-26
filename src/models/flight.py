from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from src.database import Base

    
class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(100), nullable=False)
    aircraft_type = Column(String(100), nullable=False)
    
    passenger_flights = relationship("PassengerFlight",back_populates='flights')
    def __str__(self):
        return self.route