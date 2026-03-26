from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

    
class PassengerFlight(Base):
    __tablename__ = "passenger_flight"

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    passenger_id = Column(Integer, ForeignKey("passengers.id"))
    
    flights = relationship("flights",back_populates='passenger_flight')
    passengers = relationship("passengers",back_populates='passenger_flight')