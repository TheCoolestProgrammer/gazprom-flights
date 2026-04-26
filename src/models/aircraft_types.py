from sqlalchemy import Column, Date, Integer, String, BigInteger, ForeignKey, Time
from sqlalchemy.orm import relationship
from src.database import Base


class AircraftType(Base):
    __tablename__ = "aircraft_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    flights = relationship("Flight", back_populates="aircraft_type_rel")
