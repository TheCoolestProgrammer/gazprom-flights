import enum

from sqlalchemy import Column, Date, Enum, Integer, String, BigInteger, ForeignKey, Time
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.aircraft_types import AircraftType
    
class FlightPlaneStatus(enum.Enum):
    PLANNED = "Планируется"
    IN_PROGRESS = "выполняется"
    COMPLETED = "выполнен"

class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    aircraft_type = Column(Integer, ForeignKey("aircraft_types.id"), nullable=True)
    flight_number = Column(BigInteger)
    departure_date = Column(Date)
    departure_time = Column(Time)
    place_number = Column(Integer)
    route = Column(String)
    pilot_id = Column(Integer, ForeignKey("pilots.id"), nullable=True)
    flight_status = Column(Enum(FlightPlaneStatus),nullable=False, default=FlightPlaneStatus.PLANNED)
    # flight_route_id = Column(Integer, ForeignKey("flight_routes.id"))
    # начальная и конечная точка - 2 ключа на филиалы
    # flight_date = Column(Date, nullable=False)

    passenger_flights = relationship("PassengerFlight", back_populates="flights")
    pilot = relationship("Pilot", back_populates="flights")
    aircraft_type_rel = relationship("AircraftType", back_populates="flights")
    
    # flight_routes = relationship("FlightRoute", back_populates="flights")
    def __str__(self):
        return self.route