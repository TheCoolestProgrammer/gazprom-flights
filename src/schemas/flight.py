# src/schemas/flight.py
from pydantic import BaseModel, Field
from datetime import date, time
from typing import Optional, List

class FlightCreate(BaseModel):
    aircraft_type: str
    flight_number: int
    departure_date: date
    departure_time: time
    place_number: int
    route: str
    pilot_id: Optional[int] = None

class FlightResponse(BaseModel):
    id: int
    aircraft_type: str
    flight_number: int
    departure_date: date
    departure_time: time
    place_number: int
    route: str
    pilot_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class FlightParseResponse(BaseModel):
    status: str
    message: str
    flights_parsed: int
    flights_saved: List[FlightResponse]


class FlightCreateForm(BaseModel):
    departure_date: date = Field(..., alias="departure_date")
    aircraft_type: str = Field(..., alias="aircraft_type")
    flight_number: int = Field(..., alias="flight_number")
    gzp: str = Field(..., alias="gzp")
    departure_time: time = Field(..., alias="departure_time")
    place_number: int = Field(..., alias="place_number")
    route: str = Field(..., alias="route")
    pilot_id: Optional[int] = Field(None, alias="pilot_id")
    
    class Config:
        populate_by_name = True  # позво

class SelectedFlightsRequest(BaseModel):
    flight_ids: List[int]