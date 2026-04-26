from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import aliased, joinedload
from src.models.pilot import Pilot
from src.models.airport import Airport
from src.models.passenger_flight import PassengerFlight
from src.models.flights import Flight
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import GTURelation, Passenger, RequestStatus,Gender , FlightStatus, TripPurpose
from src.models.department import Department
from src.templates_config import templates
import datetime

router = APIRouter(prefix="/dispatcher", tags=["dispatcher"])



@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
    # Параметры фильтрации
    planning_date: Optional[str] = Query(None, description="Желаемая дата"),
    flight_from: Optional[str] = Query(None, description="Откуда"),
    flight_to: Optional[str] = Query(None, description="Куда"),
    # director_status: Optional[str] = Query(None, description="Статус директора"),
    # dispatcher_status: Optional[str] = Query(None, description="Статус диспетчера"),
):
    # Получаем все рейсы
    stmt = select(Flight).where(Flight.departure_date > datetime.date.today())
    flights = session.execute(stmt).scalars().all()
    
    # Базовый запрос заявок
    query = session.query(Passenger).filter(Passenger.done_status != RequestStatus.CONFIRMED)
    airport_from = aliased(Airport)
    airport_to = aliased(Airport)

    # Применяем фильтры
    if planning_date:
        try:
            planning_date_obj = datetime.datetime.strptime(planning_date, "%Y-%m-%d").date()
            query = query.filter(Passenger.planning_date == planning_date_obj)
        except ValueError:
            pass  # Игнорируем неверный формат даты
    
    
    if flight_from:
        query = query.join(airport_from, Passenger.flight_from).filter(airport_from.name == flight_from)

    if flight_to:
        query = query.join(airport_to, Passenger.flight_to).filter(airport_to.name == flight_to)

    # if director_status:
    #     query = query.filter(Passenger.department_director_status == director_status)
    
    # if dispatcher_status:
    query = query.filter(Passenger.main_dispatcher_status == RequestStatus.CONFIRMED)
    
    # Сортируем по дате заявки (сначала новые)
    requests = query.order_by(Passenger.request_date.desc()).all()
    
    # Получаем уникальные значения для фильтров (из отфильтрованных или всех заявок)
    # Чтобы значения в выпадающих списках соответствовали текущим заявкам
    all_requests = session.query(Passenger).filter(Passenger.done_status != RequestStatus.CONFIRMED).all()
    
    unique_cities_from = set()
    unique_cities_to = set()
    # unique_director_statuses = set()
    # unique_dispatcher_statuses = set()
    
    for req in all_requests:
        if req.flight_from:
            unique_cities_from.add(req.flight_from.name)
        if req.flight_to:
            unique_cities_to.add(req.flight_to.name)
        # if req.department_director_status:
        #     unique_director_statuses.add((req.department_director_status.name, req.department_director_status.value))
        # if req.main_dispatcher_status:
        #     unique_dispatcher_statuses.add((req.main_dispatcher_status.name, req.main_dispatcher_status.value))
    
    pilots = session.query(Pilot).all()

    return templates.TemplateResponse(
        request=request, 
        name="dispatcher/dashboard.html", 
        context={
            "pilots": pilots,
            "user": user,
            "requests": requests,
            "flights": flights,
            "filters": {
                "planning_date": planning_date,
                "flight_from": flight_from,
                "flight_to": flight_to,
                # "director_status": director_status,
                # "dispatcher_status": dispatcher_status,
            },
            "unique_cities_from": sorted(list(unique_cities_from)),
            "unique_cities_to": sorted(list(unique_cities_to)),
            # "unique_director_statuses": sorted(list(unique_director_statuses)),
            # "unique_dispatcher_statuses": sorted(list(unique_dispatcher_statuses)),
        }
    )


@router.post("/change_status")
async def change_status(
    session: SessionDep,
    flight:int = Form(...),
    selected_ids: list[int] = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER))
):
    print(f"Выбранные ID для обновления: {selected_ids}")
    for i in selected_ids:
        passenger = session.get(Passenger,i)
        passenger.done_status=RequestStatus.CONFIRMED
        pf = PassengerFlight(
            passenger_id=passenger.id,
            flight_id=flight
        )
        session.add(pf)
    session.commit()

    return RedirectResponse(url="/dispatcher", status_code=303)


@router.get("/done", response_class=HTMLResponse)
async def get_done_flights(request: Request, 
                           session: SessionDep,
                           user: User = Depends(RoleChecker(Role.DISPATCHER))
                           ):
    # Загружаем связи сразу, чтобы шаблонизатор мог к ним обращаться
    flights_data = session.query(PassengerFlight).options(
        joinedload(PassengerFlight.flights),
        joinedload(PassengerFlight.passengers)
    ).all()
    
    return templates.TemplateResponse(request=request, name="dispatcher/done_flights.html", context={
        "flights": flights_data
    })


@router.post("/cancel_done")
async def cancel_done_status(
    session: SessionDep,
    passenger_id: int = Form(...),
    flight_id: int = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER))
):
    # Находим пассажира и меняем статус обратно на PENDING
    passenger = session.get(Passenger, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Пассажир не найден")
    
    passenger.done_status = RequestStatus.PENDING
    
    # Удаляем связь PassengerFlight для этого рейса
    pf = session.query(PassengerFlight).filter(
        PassengerFlight.passenger_id == passenger_id,
        PassengerFlight.flight_id == flight_id
    ).first()
    
    if pf:
        session.delete(pf)
    
    session.commit()
    
    return RedirectResponse(url="/dispatcher/done", status_code=303)

@router.post("/fly_passenger")
async def fly_passenger(
    session: SessionDep,
    passenger_id: int = Form(...),
    flight_id: int = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER))
):
    # Находим пассажира и меняем статус обратно на PENDING
    passenger = session.get(Passenger, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Пассажир не найден")
    
    passenger.flight_status = FlightStatus.FLIGHTED
    
    session.commit()
    
    return RedirectResponse(url="/dispatcher/done", status_code=303)


@router.get("/edit/{passenger_id}", response_class=HTMLResponse)
async def edit_form(
    request: Request,
    passenger_id:int,
    session: SessionDep, 
    user: User = Depends(RoleChecker(Role.DISPATCHER))
    ):
    passenger = session.query(Passenger).filter(Passenger.id==passenger_id).first()
    departments = session.query(Department).all()
    # flight_routes = session.query(FlightRoute).all()
    airports = session.query(Airport).all() 
    return templates.TemplateResponse(request=request, name="dispatcher/edit.html", context={
        "user": user,
        "departments": departments,
        "passenger":passenger,
        "airports":airports,
        # "flight_routes":flight_routes
        "TripPurpose":TripPurpose,
        "GTURelation":GTURelation
    })

@router.post("/edit/{passenger_id}")
async def edit_request(
    request: Request,
    session: SessionDep,
    passenger_id:int,
    fullname: str = Form(...),
    passport: int = Form(...),
    flight_from: int = Form(...),
    birthdate: str = Form(...),
    gender: Gender = Form(...),
    trip_purpose: TripPurpose = Form(...),
    planning_date: str = Form(...),
    flight_to: int = Form(...),
    cargo_weight:float = Form(None),
    gtu_relation:GTURelation = Form(...),
    department_id:int = Form(...),
    application_id: str = Form(...),

    notes:str = Form(None),
    user: User = Depends(RoleChecker(Role.DISPATCHER))
):
    passenger = session.get(Passenger, passenger_id)
    
    passenger.fullname=fullname
    passenger.passport=passport
    passenger.flight_from_id=flight_from
    passenger.birthdate=birthdate # Нужна конвертация в date объект
    passenger.gender=gender
    passenger.trip_purpose=trip_purpose
    passenger.status=RequestStatus.PENDING
    passenger.created_by=user.id
    passenger.planning_date=planning_date
    passenger.flight_to_id=flight_to
    passenger.cargo_weight=cargo_weight
    passenger.gtu_relation=gtu_relation
    passenger.department_id = department_id
    passenger.application_id = application_id
    passenger.notes=notes

    session.commit()
    return RedirectResponse(url="/dispatcher/", status_code=303)


@router.get("/flights", response_class=HTMLResponse)
async def flights_page(request: Request, db: SessionDep):
    flights = db.query(Flight).order_by(Flight.departure_date.desc()).all()
    pilots = db.query(Pilot).all()
    return templates.TemplateResponse(request=request, name="dispatcher/flights.html", context={
        "flights": flights,
        "pilots": pilots
    })

