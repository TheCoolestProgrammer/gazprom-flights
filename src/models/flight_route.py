from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from src.database import Base

    
class FlightRoute(Base):
    __tablename__ = "flight_routes"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(100), nullable=False)
    aircraft_type = Column(String(100), nullable=False)
    
    flights= relationship("Flight", back_populates="flight_routes")
    passengers = relationship("Passenger",back_populates="flight_routes")
    def __str__(self):
        return self.route