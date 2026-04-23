from sqlalchemy.orm import Session
from src.models.flights import Flight
from src.schemas.flight import FlightCreate
from datetime import date

def create_flight(db: Session, flight: FlightCreate):
    db_flight = Flight(
        aircraft_type=flight.aircraft_type,
        flight_number=flight.flight_number,
        departure_date=flight.departure_date,
        departure_time=flight.departure_time,
        place_number=flight.place_number,
        route=flight.route,
        pilot_id=flight.pilot_id
    )
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight

def create_flights_bulk(db: Session, flights: list[FlightCreate]):
    db_flights = []
    for flight in flights:
        db_flight = Flight(
            aircraft_type=flight.aircraft_type,
            flight_number=flight.flight_number,
            departure_date=flight.departure_date,
            departure_time=flight.departure_time,
            place_number=flight.place_number,
            route=flight.route,
            pilot_id=flight.pilot_id
        )
        db.add(db_flight)
        db_flights.append(db_flight)
    db.commit()
    for db_flight in db_flights:
        db.refresh(db_flight)
    return db_flights

def get_flights_by_date(db: Session, departure_date: date):
    return db.query(Flight).filter(Flight.departure_date == departure_date).all()