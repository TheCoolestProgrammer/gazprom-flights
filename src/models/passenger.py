from sqlalchemy import Column, Integer, String, BigInteger, Text, ForeignKey, Float, Date, Enum
from sqlalchemy.orm import relationship

import datetime

from src.database import Base

    
import enum

class Gender(enum.Enum):
    MALE="муж"
    FEMALE="жен"

class RequestStatus(enum.Enum):
    PENDING = "рассматривается"
    CONFIRMED = "разрешен"
    REJECTED = "отказ"

class TripPurpose(enum.Enum):
    SHIFT="вахта"
    BUISNESS_TRIP="служебная поездка"
    INDUSTRIAL_TRAINING="производственное обучение"
    VACATION="отпуск"
    CULTURAL_SPORT_EVENTS="культурно-спортивные мероприятия"
    PROFESSIONAL_SKILLS_COMEPETITION="конкурс профессионального мастерства"
    RVL="РВЛ"
    MEDICAL_EXAMINATION="медицинское обследование"
    COMMISION_WORK="работа коммиссии"
    CHILDREN_VACATION="детский отдых"
    OTHER="другое"

class GTURelation(enum.Enum):
    GTU_EMPLOYEE="работник ГТЮ"
    EMPLOYEE_FAMILY_MEMBER="член семьи работника"
    GTU_PENSIONER="пенсионер ГТЮ"
    OTHER_PASSENGER="сторонний пассажир"
    CULTURAL_SPORT_EVENT_MEMBER="учстник культурно-спортивного мероприятия"
    ACCOMPANYING="сопровождающий"
    GTU_CARGO="груз ГТЮ"
    OTHER_CARGO="сторонний груз"
    OTHER="другое"

class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100), nullable=False)
    birthdate = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    passport = Column(BigInteger, nullable=False)
    flight_from_id = Column(Integer, ForeignKey("departments.id"))
    # flight_route_id = Column(Integer, ForeignKey("flight_routes.id"))
    flight_to_id = Column(Integer, ForeignKey("departments.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))

    gtu_relation = Column(Enum(GTURelation), default=GTURelation.GTU_EMPLOYEE)
    trip_purpose = Column(Enum(TripPurpose), nullable=False)
    cargo_weight = Column(Float)
    notes = Column(Text, default="")
    request_date = Column(Date, default=datetime.datetime.now)
    planning_date = Column(Date)
    department_director_status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    main_dispatcher_status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    done_status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    
    created_by = Column(Integer, ForeignKey("users.id"))

    flight_from = relationship("Department",foreign_keys=[flight_from_id], back_populates="passengers_departing")
    flight_to = relationship("Department",foreign_keys=[flight_to_id], back_populates="passengers_arriving")
    departments = relationship("Department",foreign_keys=[department_id], back_populates="passengers_belong")

    passenger_flights = relationship("PassengerFlight",back_populates='passengers')
    users = relationship("User",back_populates="passengers")
    # flight_routes = relationship("FlightRoute",back_populates="passengers")
    def __str__(self):
        return self.fullname