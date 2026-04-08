from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class PassengerFlight(Base):
    __tablename__ = "passenger_flights"

    id = Column(Integer, primary_key=True, index=True)
    
    flight_id = Column(Integer, ForeignKey("flights.id"))
    passenger_id = Column(Integer, ForeignKey("passengers.id"))
    # place = Column(String(3), nullable=False)
    # flight_routes = relationship("FlightRoute",back_populates='passenger_flights')
    flights = relationship("Flight",back_populates='passenger_flights')
    passengers = relationship("Passenger",back_populates='passenger_flights')