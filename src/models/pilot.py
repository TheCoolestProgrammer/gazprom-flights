from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base


class Pilot(Base):
    __tablename__ = "pilots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    flights = relationship("Flight", back_populates="pilot")

    def __str__(self):
        return self.name
