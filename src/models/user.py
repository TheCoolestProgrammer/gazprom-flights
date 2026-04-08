from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base

import enum


class Role(enum.Enum):
    TRANSPORT_DISPATHER = "транспортный диспетчер"
    DEPARTMENT_DEIRECTOR = "директор филиала"
    DEPARTMENT_DEPUTY_DIRECTOR = "заместитель директора филиала"
    DISPATCHER = "диспетчер"
    DISPATCHER_DIRECTOR = "старший диспетчер"
    DISPATCHER_DEPUTY_DIRECTOR = "заместитель старшего диспетчера"
    ADMIN = "администратор"

    @staticmethod
    def REDIRECTION_TABLE()->dict:
        return {
            Role.ADMIN: "/admin",
            Role.DEPARTMENT_DEIRECTOR:"/department_director",
            Role.TRANSPORT_DISPATHER:"/transport_dispatcher",
            Role.DISPATCHER:"/dispatcher",
            Role.DISPATCHER_DIRECTOR:"/main_dispatcher"
        }

    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True)
    department_id = Column(Integer,ForeignKey("departments.id"))

    role = Column(Enum(Role), nullable=False, default=Role.DISPATCHER)
    passengers = relationship("Passenger",back_populates="users")
    departments = relationship("Department",back_populates="users")