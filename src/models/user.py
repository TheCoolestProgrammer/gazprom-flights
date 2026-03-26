from sqlalchemy import Column, Integer, String, Enum

from src.database import Base

import enum


class Role(enum.Enum):
    TRANSPORT_DISPATHER = "transport_dispatcher"
    DEPARTMENT_DEIRECTOR = "department_director"
    DEPARTMENT_DEPUTY_DIRECTOR = "department_deputy_director"
    DISPATCHER = "dispatcher"
    DISPATCHER_DIRECTOR = "dispatcher_director"
    DISPATCHER_DEPUTY_DIRECTOR = "dispatcher_deputy_director"
    ADMIN = "admin"
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True)

    role = Column(Enum(Role), nullable=False)
