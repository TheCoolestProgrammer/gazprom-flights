from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from src.database import Base

    
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(BigInteger, nullable=False)

    passengers = relationship("Passenger",back_populates='departments')
    users = relationship("User",back_populates="departments")
    
    def __str__(self):
        return self.name