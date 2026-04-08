from sqlalchemy import Column, Date, Integer, String, BigInteger, ForeignKey, Time
from sqlalchemy.orm import relationship
from src.database import Base

    
class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    aircraft_type = Column(String)
    flight_number = Column(BigInteger)
    departure_time = Column(Time)
    place_number = Column(Integer)
    route=Column(String)
    # flight_route_id = Column(Integer, ForeignKey("flight_routes.id"))
    # начальная и конечная точка - 2 ключа на филиалы
    # flight_date = Column(Date, nullable=False)

    passenger_flights = relationship("PassengerFlight",back_populates="flights")
    # flight_routes = relationship("FlightRoute", back_populates="flights")
    def __str__(self):
        return self.route