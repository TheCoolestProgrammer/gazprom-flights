# src/schemas/flight.py
from pydantic import BaseModel
from datetime import date, time
from typing import Optional, List

class FlightCreate(BaseModel):
    aircraft_type: str
    flight_number: int
    departure_date: date
    departure_time: time
    place_number: int
    route: str

class FlightResponse(BaseModel):
    id: int
    aircraft_type: str
    flight_number: int
    departure_date: date
    departure_time: time
    place_number: int
    route: str
    
    class Config:
        from_attributes = True

class FlightParseResponse(BaseModel):
    status: str
    message: str
    flights_parsed: int
    flights_saved: List[FlightResponse]