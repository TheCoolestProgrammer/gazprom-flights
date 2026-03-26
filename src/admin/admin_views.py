from sqladmin import ModelView
from src.models.user import User, Role
from src.models.department import Department
from src.models.flight import Flight
from src.models.passenger import Passenger
from src.models.passenger_flight import PassengerFlight

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.login, User.name, User.role, User.email]
    column_searchable_list = [User.login, User.name, User.email]
    icon = "fa-solid fa-user"
    name = "Пользователь"
    name_plural = "Пользователи"

class DepartmentAdmin(ModelView, model=Department):
    column_list = [Department.id, Department.name, Department.phone]
    form_excluded_columns = ["passengers"]
    icon = "fa-solid fa-building"
    name = "филиал"
    name_plural = "филиалы"

class FlightAdmin(ModelView, model=Flight):
    column_list = [Flight.id, Flight.route, Flight.aircraft_type]
    form_excluded_columns = ["passengers", "passenger_flights"]
    icon = "fa-solid fa-plane"
    name = "Рейс"
    name_plural = "Рейсы"

class PassengerAdmin(ModelView, model=Passenger):
    # Колонки в таблице
    column_list = [
        Passenger.id, 
        Passenger.fullname, 
        Passenger.passport, 
        # Passenger.department_id
        "departments"
    ]

    # Поля в форме создания/редактирования
    form_columns = [
        Passenger.fullname,
        Passenger.birthdate,
        Passenger.gender,
        Passenger.passport,
        # Passenger.department_id,
        "departments",
        Passenger.trip_purpose,
        Passenger.cargo_weight,
        Passenger.notes,
        Passenger.fact_date
    ]
    
    icon = "fa-solid fa-person-walking-luggage"
    name = "Пассажир"
    name_plural = "Пассажиры"

class PassengerFlightAdmin(ModelView, model=PassengerFlight):
    column_list = [
        PassengerFlight.id,
        # PassengerFlight.flight_id,
        "flights",
        # PassengerFlight.passenger_id
        "passengers"
        ]
    icon = "fa-solid fa-ticket"
    name = "Билет/Связь"
    name_plural = "Связи Рейс-Пассажир"