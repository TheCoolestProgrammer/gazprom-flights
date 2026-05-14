from typing import Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request, Depends, Form, status
from fastapi import Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import case, func, select
from sqlalchemy.orm import aliased, joinedload
from src.models.cargo import Cargo, CargoLocation, PackagingType
from src.models.aircraft_types import AircraftType
from src.models.pilot import Pilot
from src.models.airport import Airport
from src.models.passenger_flight import PassengerFlight
from src.models.flights import Flight, FlightPlaneStatus
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import (
    GTURelation,
    Passenger,
    RequestStatus,
    Gender,
    FlightStatus,
    TripPurpose,
)
from src.models.department import Department
from src.templates_config import templates
import datetime

router = APIRouter(prefix="/dispatcher", tags=["dispatcher"])


@router.get("/edit-cargo/{cargo_id}", response_class=HTMLResponse)
async def cargo_edit_form(
    request: Request,
    cargo_id: int,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER_DIRECTOR)),
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Груз не найден"
        )

    airports = session.query(Airport).all()
    return templates.TemplateResponse(
        request=request,
        name="main_dispatcher/cargo_edit.html",
        context={
            "user": user,
            "cargo": cargo,
            "airports": airports,
            "PackagingType": PackagingType,
            "CargoLocation": CargoLocation,
        },
    )


@router.get("/done-cargo", response_class=HTMLResponse)
async def done_cargo_dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
    planning_date: Optional[str] = Query(None, description="Желаемая дата"),
    flight_from: Optional[str] = Query(None, description="Откуда"),
    flight_to: Optional[str] = Query(None, description="Куда"),
):
    query = session.query(Cargo)
    airport_from = aliased(Airport)
    airport_to = aliased(Airport)

    query = query.filter(
        Cargo.department_director_status == RequestStatus.CONFIRMED,
        # Cargo.main_dispatcher_status == RequestStatus.CONFIRMED,
        Cargo.done_status == RequestStatus.CONFIRMED,
    )

    if planning_date:
        try:
            planning_date_obj = datetime.strptime(planning_date, "%Y-%m-%d").date()
            query = query.filter(Cargo.planning_date == planning_date_obj)
        except ValueError:
            pass

    if flight_from:
        query = query.join(airport_from, Cargo.flight_from).filter(
            airport_from.name == flight_from
        )

    if flight_to:
        query = query.join(airport_to, Cargo.flight_to).filter(
            airport_to.name == flight_to
        )

    status_order = case(
        (Cargo.main_dispatcher_status == RequestStatus.PENDING, 1),
        (Cargo.main_dispatcher_status == RequestStatus.CONFIRMED, 2),
        (Cargo.main_dispatcher_status == RequestStatus.REJECTED, 4),
        else_=5,
    )
    cargo_requests = (
        query.options(
            joinedload(Cargo.flight)
            .joinedload(Flight.passenger_flights)
            .joinedload(PassengerFlight.passengers)
        )
        .order_by(status_order, Cargo.request_date.desc())
        .all()
    )

    flights = (
        session.query(Flight)
        .order_by(Flight.departure_date, Flight.departure_time)
        .all()
    )

    all_cargo = session.query(Cargo).all()
    unique_cities_from = set()
    unique_cities_to = set()

    for item in all_cargo:
        if item.flight_from:
            unique_cities_from.add(item.flight_from.name)
        if item.flight_to:
            unique_cities_to.add(item.flight_to.name)

    return templates.TemplateResponse(
        request=request,
        name="dispatcher/done_cargo.html",
        context={
            "user": user,
            "cargo_requests": cargo_requests,
            "flights": flights,
            "Status": RequestStatus,
            "filters": {
                "planning_date": planning_date,
                "flight_from": flight_from,
                "flight_to": flight_to,
            },
            "unique_cities_from": sorted(unique_cities_from),
            "unique_cities_to": sorted(unique_cities_to),
        },
    )


@router.post("/cancel_done_cargo")
async def cancel_done_cargo(
    session: SessionDep,
    cargo_id: int = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Груз не найден"
        )
    cargo.done_status = RequestStatus.PENDING
    session.commit()
    return RedirectResponse(url="/dispatcher/done-cargo", status_code=303)


@router.post("/fly_cargo")
async def fly_cargo(
    session: SessionDep,
    cargo_id: int = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Груз не найден"
        )
    cargo.flight_status = FlightStatus.FLIGHTED
    session.commit()
    return RedirectResponse(url="/dispatcher/done-cargo", status_code=303)


@router.post("/assign_cargo_flight")
async def assign_cargo_flight(
    session: SessionDep,
    cargo_id: int = Form(...),
    flight_id: Optional[str] = Form(None),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Груз не найден"
        )
    if flight_id:
        try:
            flight_int = int(flight_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный ID рейса"
            )
        flight = session.get(Flight, flight_int)
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден"
            )
        cargo.flight_id = flight_int
    else:
        cargo.flight_id = None
    session.commit()
    return RedirectResponse(url="/dispatcher/done-cargo", status_code=303)


@router.post("/cargo/assign_flight")
async def assign_cargo_flight_batch(
    session: SessionDep,
    selected_ids: list[int] = Form(...),
    flight_id: Optional[str] = Form(None),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    if not selected_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Выберите хотя бы один груз"
        )
    flight_int = None
    if flight_id:
        try:
            flight_int = int(flight_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный ID рейса"
            )
        flight = session.get(Flight, flight_int)
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Рейс не найден"
            )
    for cargo_id in selected_ids:
        cargo = session.get(Cargo, cargo_id)
        if cargo:
            cargo.flight_id = flight_int
    session.commit()
    return RedirectResponse(url="/dispatcher/cargo", status_code=303)


@router.get("/cargo", response_class=HTMLResponse)
async def cargo_dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
    planning_date: Optional[str] = Query(None, description="Желаемая дата"),
    flight_from: Optional[str] = Query(None, description="Откуда"),
    flight_to: Optional[str] = Query(None, description="Куда"),
):
    query = session.query(Cargo)
    airport_from = aliased(Airport)
    airport_to = aliased(Airport)

    query = query.filter(
        Cargo.department_director_status == RequestStatus.CONFIRMED,
        # Cargo.main_dispatcher_status == RequestStatus.CONFIRMED,
        Cargo.done_status != RequestStatus.CONFIRMED,
    )

    if planning_date:
        try:
            planning_date_obj = datetime.strptime(planning_date, "%Y-%m-%d").date()
            query = query.filter(Cargo.planning_date == planning_date_obj)
        except ValueError:
            pass

    if flight_from:
        query = query.join(airport_from, Cargo.flight_from).filter(
            airport_from.name == flight_from
        )

    if flight_to:
        query = query.join(airport_to, Cargo.flight_to).filter(
            airport_to.name == flight_to
        )

    status_order = case(
        (Cargo.main_dispatcher_status == RequestStatus.PENDING, 1),
        (Cargo.main_dispatcher_status == RequestStatus.CONFIRMED, 2),
        # (Cargo.main_dispatcher_status == RequestStatus.SOVP, 3),
        (Cargo.main_dispatcher_status == RequestStatus.REJECTED, 4),
        else_=5,
    )
    cargo_requests = (
        query.options(joinedload(Cargo.flight))
        .order_by(status_order, Cargo.request_date.desc())
        .all()
    )

    flights = (
        session.query(Flight)
        .order_by(Flight.departure_date, Flight.departure_time)
        .all()
    )
    all_cargo = session.query(Cargo).all()
    unique_cities_from = set()
    unique_cities_to = set()

    for item in all_cargo:
        if item.flight_from:
            unique_cities_from.add(item.flight_from.name)
        if item.flight_to:
            unique_cities_to.add(item.flight_to.name)

    return templates.TemplateResponse(
        request=request,
        name="dispatcher/cargo.html",
        context={
            "user": user,
            "cargo_requests": cargo_requests,
            "flights": flights,
            "Status": RequestStatus,
            "filters": {
                "planning_date": planning_date,
                "flight_from": flight_from,
                "flight_to": flight_to,
            },
            "unique_cities_from": sorted(unique_cities_from),
            "unique_cities_to": sorted(unique_cities_to),
        },
    )


@router.post("/cargo/change_done_status_batch")
async def change_cargo_done_status_batch(
    session: SessionDep,
    selected_ids: list[int] = Form(...),
    action: str = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    if action == "done":
        new_status = RequestStatus.CONFIRMED
    else:
        new_status = RequestStatus.PENDING

    for cargo_id in selected_ids:
        cargo = session.get(Cargo, cargo_id)
        if cargo:
            cargo.done_status = new_status
    session.commit()
    return RedirectResponse(url="/dispatcher/cargo", status_code=303)


@router.patch("/cargo/done_status/{cargo_id}")
async def change_cargo_done_status(
    cargo_id: int,
    session: SessionDep,
    request_status: str = Body(..., embed=True),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Груз с ID {cargo_id} не найден",
        )
    try:
        new_status = RequestStatus(request_status)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid request status: {request_status}"
        )
    cargo.done_status = new_status
    session.commit()
    return JSONResponse(content={"message": "Done status updated"})


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
    query = session.query(Passenger).filter(
        Passenger.done_status != RequestStatus.CONFIRMED
    )
    airport_from = aliased(Airport)
    airport_to = aliased(Airport)

    # Применяем фильтры
    if planning_date:
        try:
            planning_date_obj = datetime.datetime.strptime(
                planning_date, "%Y-%m-%d"
            ).date()
            query = query.filter(Passenger.planning_date == planning_date_obj)
        except ValueError:
            pass  # Игнорируем неверный формат даты

    if flight_from:
        query = query.join(airport_from, Passenger.flight_from).filter(
            airport_from.name == flight_from
        )

    if flight_to:
        query = query.join(airport_to, Passenger.flight_to).filter(
            airport_to.name == flight_to
        )

    # if director_status:
    #     query = query.filter(Passenger.department_director_status == director_status)

    # if dispatcher_status:
    # query = query.filter(Passenger.main_dispatcher_status == RequestStatus.CONFIRMED)
    query = query.filter(
        Passenger.department_director_status == RequestStatus.CONFIRMED
    )
    # Сортируем по дате заявки (сначала новые)
    requests = query.order_by(Passenger.request_date.desc()).all()

    # Получаем уникальные значения для фильтров (из отфильтрованных или всех заявок)
    # Чтобы значения в выпадающих списках соответствовали текущим заявкам
    all_requests = (
        session.query(Passenger)
        .filter(Passenger.done_status != RequestStatus.CONFIRMED)
        .all()
    )

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
    aircraft_types = session.query(AircraftType).all()

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
            "aircraft_types": aircraft_types,
        },
    )


@router.post("/change_status")
async def change_status(
    session: SessionDep,
    flight: int = Form(...),
    selected_ids: list[int] = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    print(f"Выбранные ID для обновления: {selected_ids}")
    for i in selected_ids:
        passenger = session.get(Passenger, i)
        passenger.done_status = RequestStatus.CONFIRMED
        pf = PassengerFlight(passenger_id=passenger.id, flight_id=flight)
        session.add(pf)
    session.commit()

    return RedirectResponse(url="/dispatcher", status_code=303)


@router.get("/done", response_class=HTMLResponse)
async def get_done_flights(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
    # Параметры фильтрации
    departure_date: Optional[str] = Query(None, description="Дата вылета"),
    route: Optional[str] = Query(None, description="Маршрут"),
    flight_number: Optional[str] = Query(None, description="Номер рейса"),
    aircraft_type: Optional[str] = Query(None, description="Тип ВС"),
    flight_status: Optional[str] = Query(None, description="Статус пассажира"),
):
    # Загружаем связи сразу, чтобы шаблонизатор мог к ним обращаться
    query = (
        session.query(PassengerFlight)
        .options(
            joinedload(PassengerFlight.flights), joinedload(PassengerFlight.passengers)
        )
        .join(Flight, PassengerFlight.flight_id == Flight.id)
    )

    # Применяем фильтры
    if departure_date:
        try:
            departure_date_obj = datetime.datetime.strptime(
                departure_date, "%Y-%m-%d"
            ).date()
            query = query.filter(
                PassengerFlight.flights.has(Flight.departure_date == departure_date_obj)
            )
        except ValueError:
            pass

    if route:
        query = query.filter(
            PassengerFlight.flights.has(Flight.route.ilike(f"%{route}%"))
        )

    if flight_number:
        try:
            flight_number_value = int(flight_number)
            query = query.filter(
                PassengerFlight.flights.has(Flight.flight_number == flight_number_value)
            )
        except ValueError:
            pass

    if aircraft_type:
        try:
            aircraft_type_value = int(aircraft_type)
            query = query.filter(
                PassengerFlight.flights.has(Flight.aircraft_type == aircraft_type_value)
            )
        except ValueError:
            pass

    if flight_status:
        try:
            flight_status_value = FlightStatus(flight_status)
            query = query.filter(
                PassengerFlight.passengers.has(
                    Passenger.flight_status == flight_status_value
                )
            )
        except ValueError:
            pass

    # Сортировка: сначала не вылетевшие, потом вылетевшие
    from sqlalchemy import case

    status_order = case(
        (
            PassengerFlight.passengers.has(
                Passenger.flight_status == FlightStatus.NOT_FLIGHTED
            ),
            1,
        ),
        (
            PassengerFlight.passengers.has(
                Passenger.flight_status == FlightStatus.FLIGHTED
            ),
            2,
        ),
        else_=3,
    )
    flights_data = query.order_by(status_order, Flight.departure_date.desc()).all()

    # Получаем уникальные значения для фильтров
    all_flights = (
        session.query(PassengerFlight)
        .options(
            joinedload(PassengerFlight.flights), joinedload(PassengerFlight.passengers)
        )
        .all()
    )

    aircraft_types = session.query(AircraftType).all()
    for i in flights_data:
        print(i.passengers.trip_purpose)
    return templates.TemplateResponse(
        request=request,
        name="dispatcher/done_flights.html",
        context={
            "flights": flights_data,
            "aircraft_types": aircraft_types,
            "flight_statuses": FlightStatus,
            "filters": {
                "departure_date": departure_date,
                "route": route,
                "flight_number": flight_number,
                "aircraft_type": aircraft_type,
                "flight_status": flight_status,
            },
        },
    )


@router.post("/cancel_done")
async def cancel_done_status(
    session: SessionDep,
    passenger_id: int = Form(...),
    flight_id: int = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    # Находим пассажира и меняем статус обратно на PENDING
    passenger = session.get(Passenger, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Пассажир не найден")

    passenger.done_status = RequestStatus.PENDING

    # Удаляем связь PassengerFlight для этого рейса
    pf = (
        session.query(PassengerFlight)
        .filter(
            PassengerFlight.passenger_id == passenger_id,
            PassengerFlight.flight_id == flight_id,
        )
        .first()
    )

    if pf:
        session.delete(pf)

    session.commit()

    return RedirectResponse(url="/dispatcher/done", status_code=303)


@router.post("/fly_passenger")
async def fly_passenger(
    session: SessionDep,
    passenger_id: int = Form(...),
    flight_id: int = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
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
    passenger_id: int,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    passenger = session.query(Passenger).filter(Passenger.id == passenger_id).first()
    departments = session.query(Department).all()
    # flight_routes = session.query(FlightRoute).all()
    airports = session.query(Airport).all()
    return templates.TemplateResponse(
        request=request,
        name="dispatcher/edit.html",
        context={
            "user": user,
            "departments": departments,
            "passenger": passenger,
            "airports": airports,
            # "flight_routes":flight_routes
            "TripPurpose": TripPurpose,
            "GTURelation": GTURelation,
        },
    )


@router.post("/edit/{passenger_id}")
async def edit_request(
    request: Request,
    session: SessionDep,
    passenger_id: int,
    fullname: str = Form(...),
    passport: int = Form(...),
    flight_from: int = Form(...),
    birthdate: str = Form(...),
    gender: Gender = Form(...),
    trip_purpose: TripPurpose = Form(...),
    # planning_date: str = Form(...),
    flight_to: int = Form(...),
    cargo_weight: float = Form(None),
    gtu_relation: GTURelation = Form(...),
    # department_id:int = Form(...),
    application_id: str = Form(...),
    notes: str = Form(None),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    passenger = session.get(Passenger, passenger_id)

    passenger.fullname = fullname
    passenger.passport = passport
    passenger.flight_from_id = flight_from
    passenger.birthdate = birthdate  # Нужна конвертация в date объект
    passenger.gender = gender
    passenger.trip_purpose = trip_purpose
    passenger.status = RequestStatus.PENDING
    passenger.created_by = user.id
    # passenger.planning_date = planning_date
    passenger.flight_to_id = flight_to
    passenger.cargo_weight = cargo_weight
    passenger.gtu_relation = gtu_relation
    # passenger.department_id = department_id
    passenger.application_id = application_id
    passenger.notes = notes

    session.commit()
    return RedirectResponse(url="/dispatcher/", status_code=303)


@router.get("/edit_flight/{flight_id}", response_class=HTMLResponse)
async def edit_flight_form(
    request: Request,
    flight_id: int,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Рейс не найден")

    pilots = session.query(Pilot).all()
    aircraft_types = session.query(AircraftType).all()

    return templates.TemplateResponse(
        request=request,
        name="dispatcher/edit_flight.html",
        context={
            "user": user,
            "flight": flight,
            "pilots": pilots,
            "aircraft_types": aircraft_types,
            "flight_statuses": FlightPlaneStatus,
        },
    )


@router.post("/edit_flight/{flight_id}")
async def edit_flight_request(
    request: Request,
    session: SessionDep,
    flight_id: int,
    aircraft_type: int = Form(...),
    flight_number: int = Form(...),
    departure_date: str = Form(...),
    departure_time: str = Form(...),
    place_number: int = Form(...),
    route: str = Form(...),
    pilot_id: str | None = Form(None),
    notes: str = Form(None),
    # flight_status: FlightPlaneStatus = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER)),
):
    flight = session.get(Flight, flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Рейс не найден")

    if pilot_id:
        try:
            pilot_id_value = int(pilot_id)
        except ValueError:
            pilot_id_value = None
    else:
        pilot_id_value = None

    flight.aircraft_type = aircraft_type
    flight.flight_number = flight_number
    flight.departure_date = datetime.datetime.strptime(
        departure_date, "%Y-%m-%d"
    ).date()
    flight.departure_time = datetime.time.fromisoformat(departure_time)
    flight.place_number = place_number
    flight.route = route
    flight.pilot_id = pilot_id_value
    flight.notes = notes
    # flight.flight_status = flight_status

    session.commit()
    return RedirectResponse(url="/dispatcher/flights", status_code=303)


@router.get("/flights", response_class=HTMLResponse)
async def flights_page(
    request: Request,
    db: SessionDep,
    departure_date: Optional[str] = Query(None, description="Дата вылета"),
    route: Optional[str] = Query(None, description="Маршрут"),
    flight_number: Optional[str] = Query(None, description="Номер рейса"),
    aircraft_type: Optional[str] = Query(None, description="Тип ВС"),
    flight_status: Optional[str] = Query(None, description="Статус рейса"),
):
    # Основной запрос к рейсам
    flight_query = db.query(Flight)

    if departure_date:
        try:
            departure_date_obj = datetime.datetime.strptime(
                departure_date, "%Y-%m-%d"
            ).date()
            flight_query = flight_query.filter(
                Flight.departure_date == departure_date_obj
            )
        except ValueError:
            pass

    if route:
        flight_query = flight_query.filter(Flight.route.ilike(f"%{route}%"))

    if flight_number:
        try:
            flight_number_value = int(flight_number)
            flight_query = flight_query.filter(
                Flight.flight_number == flight_number_value
            )
        except ValueError:
            pass

    if aircraft_type:
        try:
            aircraft_type_value = int(aircraft_type)
            flight_query = flight_query.filter(
                Flight.aircraft_type == aircraft_type_value
            )
        except ValueError:
            pass

    if flight_status:
        try:
            flight_status_value = FlightPlaneStatus(flight_status)
            flight_query = flight_query.filter(
                Flight.flight_status == flight_status_value
            )
        except ValueError:
            pass

    # Получаем отфильтрованные рейсы
    flights_raw = flight_query.order_by(Flight.departure_date.desc()).all()

    # Для каждого рейса вычисляем статистику
    flights_with_stats = []
    for flight in flights_raw:
        # Подсчет пассажиров и их веса
        passenger_data = (
            db.query(
                func.count(Passenger.id).label("p_count"),
                func.coalesce(func.sum(Passenger.cargo_weight), 0).label("p_weight"),
            )
            .join(PassengerFlight, Passenger.id == PassengerFlight.passenger_id)
            .filter(PassengerFlight.flight_id == flight.id)
            .first()
        )

        # Подсчет грузов и их веса
        cargo_data = (
            db.query(
                func.coalesce(func.sum(Cargo.places_count), 0).label("c_places"),
                func.coalesce(func.sum(Cargo.weight), 0).label("c_weight"),
            )
            .filter(Cargo.flight_id == flight.id)
            .first()
        )

        passenger_count = passenger_data.p_count or 0
        passenger_weight = float(passenger_data.p_weight or 0)
        cargo_places = int(cargo_data.c_places or 0)
        cargo_weight = float(cargo_data.c_weight or 0)

        # Общее количество (пассажиры + места грузов)
        total_count = passenger_count + cargo_places
        # Общий вес (вес грузов пассажиров + вес грузов)
        total_weight = passenger_weight + cargo_weight

        flights_with_stats.append((flight, total_count, total_weight))

    pilots = db.query(Pilot).all()
    aircraft_types = db.query(AircraftType).all()

    return templates.TemplateResponse(
        request=request,
        name="dispatcher/flights.html",
        context={
            "flights": flights_with_stats,
            "pilots": pilots,
            "flight_statuses": FlightPlaneStatus,
            "filters": {
                "departure_date": departure_date,
                "route": route,
                "flight_number": flight_number,
                "aircraft_type": aircraft_type,
                "flight_status": flight_status,
            },
            "aircraft_types": aircraft_types,
        },
    )


@router.post("/flights/{flight_id}/change_status")
async def change_flight_status(
    request: Request,
    db: SessionDep,
    flight_id: int,
    status: FlightPlaneStatus = Body(..., embed=True),
):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Рейс не найден")
    flight.flight_status = status
    db.commit()
    return JSONResponse(
        content={
            "message": "Статус рейса обновлен",
            "new_status": flight.flight_status.value,
        },
        status_code=200,
    )
