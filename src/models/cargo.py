from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
import datetime
from src.database import Base
from src.models.passenger import RequestStatus


class PackagingType(enum.Enum):
    BOX = "ящик"
    PALLET = "паллет"
    BAG = "мешок"
    CONTAINER = "контейнер"
    OTHER = "другое"


class CargoLocation(enum.Enum):
    OUTSIDE = "на внешней подложке"
    INSIDE = "внутри фюзеляжа"


class Cargo(Base):
    __tablename__ = "cargo_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    packaging_type = Column(Enum(PackagingType), nullable=False)
    flight_from_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    flight_to_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    places_count = Column(Integer, nullable=False, default=1)
    weight = Column(Float, nullable=False)
    hazardous = Column(Boolean, nullable=False, default=False)
    department_director_status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    main_dispatcher_status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    done_status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    location = Column(Enum(CargoLocation), nullable=False)
    planning_date = Column(Date, nullable=False)
    main_dispatcher_date = Column(Date, nullable=True)
    request_date = Column(Date, default=datetime.datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=True)

    flight_from = relationship("Airport", foreign_keys=[flight_from_id])
    flight_to = relationship("Airport", foreign_keys=[flight_to_id])
    departments = relationship("Department", foreign_keys=[department_id])
    flight = relationship("Flight", back_populates="cargo_items")

    def __str__(self):
        return self.name
