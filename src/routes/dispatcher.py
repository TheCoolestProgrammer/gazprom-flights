from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.models.passenger_flight import PassengerFlight
from src.models.flights import Flight
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender 
from src.models.department import Department
import datetime

router = APIRouter(prefix="/dispatcher", tags=["dispatcher"])
templates = Jinja2Templates(directory="templates")



@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
    # Параметры фильтрации
    planning_date: Optional[str] = Query(None, description="Желаемая дата"),
    flight_from: Optional[str] = Query(None, description="Откуда"),
    flight_to: Optional[str] = Query(None, description="Куда"),
    director_status: Optional[str] = Query(None, description="Статус директора"),
    dispatcher_status: Optional[str] = Query(None, description="Статус диспетчера"),
):
    # Получаем все рейсы
    stmt = select(Flight).where(Flight.departure_date > datetime.date.today())
    flights = session.execute(stmt).scalars().all()
    
    # Базовый запрос заявок
    query = session.query(Passenger).filter(Passenger.done_status != RequestStatus.CONFIRMED)
    
    # Применяем фильтры
    if planning_date:
        try:
            planning_date_obj = datetime.datetime.strptime(planning_date, "%Y-%m-%d").date()
            query = query.filter(Passenger.planning_date == planning_date_obj)
        except ValueError:
            pass  # Игнорируем неверный формат даты
    
    if flight_from:
        query = query.join(Passenger.flight_from).filter(Department.name == flight_from)
    
    if flight_to:
        query = query.join(Passenger.flight_to).filter(Department.name == flight_to)
    
    if director_status:
        query = query.filter(Passenger.department_director_status == director_status)
    
    if dispatcher_status:
        query = query.filter(Passenger.main_dispatcher_status == dispatcher_status)
    
    # Сортируем по дате заявки (сначала новые)
    requests = query.order_by(Passenger.request_date.desc()).all()
    
    # Получаем уникальные значения для фильтров (из отфильтрованных или всех заявок)
    # Чтобы значения в выпадающих списках соответствовали текущим заявкам
    all_requests = session.query(Passenger).filter(Passenger.done_status != RequestStatus.CONFIRMED).all()
    
    unique_cities_from = set()
    unique_cities_to = set()
    unique_director_statuses = set()
    unique_dispatcher_statuses = set()
    
    for req in all_requests:
        if req.flight_from:
            unique_cities_from.add(req.flight_from.name)
        if req.flight_to:
            unique_cities_to.add(req.flight_to.name)
        if req.department_director_status:
            unique_director_statuses.add((req.department_director_status.name, req.department_director_status.value))
        if req.main_dispatcher_status:
            unique_dispatcher_statuses.add((req.main_dispatcher_status.name, req.main_dispatcher_status.value))
    
    return templates.TemplateResponse(
        request=request, 
        name="dispatcher/dashboard.html", 
        context={
            "user": user,
            "requests": requests,
            "flights": flights,
            "filters": {
                "planning_date": planning_date,
                "flight_from": flight_from,
                "flight_to": flight_to,
                "director_status": director_status,
                "dispatcher_status": dispatcher_status,
            },
            "unique_cities_from": sorted(list(unique_cities_from)),
            "unique_cities_to": sorted(list(unique_cities_to)),
            "unique_director_statuses": sorted(list(unique_director_statuses)),
            "unique_dispatcher_statuses": sorted(list(unique_dispatcher_statuses)),
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