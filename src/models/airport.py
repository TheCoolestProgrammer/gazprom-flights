from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.passenger import Passenger
    
class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    passengers_departing = relationship("Passenger",foreign_keys=[Passenger.flight_from_id],back_populates='flight_from')
    passengers_arriving = relationship("Passenger",foreign_keys=[Passenger.flight_to_id],back_populates='flight_to')
  
    def __str__(self):
        return self.name