from alembic.environment import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import joinedload
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
# from src.models.flight_route import FlightRoute
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender,TripPurpose, GTURelation
from src.models.department import Department
from src.models.airport import Airport
from src.models.passenger_flight import PassengerFlight
from src.models.cargo import Cargo, PackagingType, CargoLocation
from src.templates_config import templates

router = APIRouter(prefix="/transport_dispatcher", tags=["transport_dispatcher"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
    ):
    requests = session.query(Passenger).filter(Passenger.department_id==user.department_id).options(
        joinedload(Passenger.passenger_flights).joinedload(PassengerFlight.flights)
    ).order_by(Passenger.request_date.desc()).all()
    return templates.TemplateResponse(request=request, name="transport_dispatcher/dashboard.html", context={
        "user": user,
        "requests": requests
    })

@router.get("/create", response_class=HTMLResponse)
async def create_form(
    request: Request,
    session: SessionDep, 
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER)) 
    ):
    # flight_routes = session.query(Department).all()
    departments = session.query(Department).all()
    airports = session.query(Airport).all()
    return templates.TemplateResponse(request=request, name="transport_dispatcher/create.html", context={
        "user": user,
        "departments": departments,
        "airports":airports,
        # "flight_routes":flight_routes
        "TripPurpose":TripPurpose,
        "GTURelation":GTURelation
    })

@router.post("/create")
async def create_request(
    request: Request,
    session: SessionDep,
    fullname: str = Form(...),
    passport: int = Form(...),
    flight_from: int = Form(...),
    birthdate: str = Form(...),
    gender: Gender = Form(...),
    trip_purpose: TripPurpose = Form(...),
    planning_date: str = Form(...),
    flight_to: int = Form(...),
    gtu_relation:GTURelation = Form(...),
    # department_id:int = Form(...),
    application_id: str = Form(...),
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    new_passenger = Passenger(
        fullname=fullname,
        passport=passport,
        flight_to_id=flight_to,
        birthdate=birthdate,
        gender=gender,
        trip_purpose=trip_purpose,
        # status=RequestStatus.PENDING,
        created_by=user.id,
        planning_date=planning_date,
        flight_from_id=flight_from,
        gtu_relation=gtu_relation,
        # department_id=department_id,
        department_id=user.department_id,
        application_id=application_id
    )
    session.add(new_passenger)
    session.commit()
    return RedirectResponse(url="/transport_dispatcher/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/cargo", response_class=HTMLResponse)
async def cargo_dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
    ):
    cargo_requests = session.query(Cargo).filter(Cargo.department_id==user.department_id).order_by(Cargo.request_date.desc()).all()
    return templates.TemplateResponse(request=request, name="transport_dispatcher/cargo_dashboard.html", context={
        "user": user,
        "cargo_requests": cargo_requests
    })

@router.get("/cargo/create", response_class=HTMLResponse)
async def cargo_create_form(
    request: Request,
    session: SessionDep, 
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER)) 
    ):
    airports = session.query(Airport).all()
    return templates.TemplateResponse(request=request, name="transport_dispatcher/cargo_create.html", context={
        "user": user,
        "airports": airports,
        "PackagingType": PackagingType,
        "CargoLocation": CargoLocation
    })

@router.post("/cargo/create")
async def create_cargo(
    request: Request,
    session: SessionDep,
    cargo_name: str = Form(...),
    packaging_type: PackagingType = Form(...),
    flight_from: int = Form(...),
    flight_to: int = Form(...),
    places_count: int = Form(...),
    weight: float = Form(...),
    hazardous: bool = Form(False),
    location: CargoLocation = Form(...),
    planning_date: str = Form(...),
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    new_cargo = Cargo(
        name=cargo_name,
        packaging_type=packaging_type,
        flight_from_id=flight_from,
        flight_to_id=flight_to,
        places_count=places_count,
        weight=weight,
        hazardous=hazardous,
        location=location,
        planning_date=planning_date,
        created_by=user.id,
        department_id=user.department_id
    )
    session.add(new_cargo)
    session.commit()
    return RedirectResponse(url="/transport_dispatcher/cargo", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/cargo/edit/{cargo_id}", response_class=HTMLResponse)
async def cargo_edit_form(
    request: Request,
    cargo_id: int,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo or cargo.department_id != user.department_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Груз не найден")

    airports = session.query(Airport).all()
    return templates.TemplateResponse(request=request, name="transport_dispatcher/cargo_edit.html", context={
        "user": user,
        "cargo": cargo,
        "airports": airports,
        "PackagingType": PackagingType,
        "CargoLocation": CargoLocation
    })


@router.post("/cargo/edit/{cargo_id}")
async def edit_cargo(
    request: Request,
    session: SessionDep,
    cargo_id: int,
    cargo_name: str = Form(...),
    packaging_type: PackagingType = Form(...),
    flight_from: int = Form(...),
    flight_to: int = Form(...),
    places_count: int = Form(...),
    weight: float = Form(...),
    hazardous: bool = Form(False),
    location: CargoLocation = Form(...),
    planning_date: str = Form(...),
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo or cargo.department_id != user.department_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Груз не найден")

    cargo.name = cargo_name
    cargo.packaging_type = packaging_type
    cargo.flight_from_id = flight_from
    cargo.flight_to_id = flight_to
    cargo.places_count = places_count
    cargo.weight = weight
    cargo.hazardous = hazardous
    cargo.location = location
    cargo.planning_date = planning_date

    session.commit()
    return RedirectResponse(url="/transport_dispatcher/cargo", status_code=status.HTTP_303_SEE_OTHER)


@router.delete("/cargo/delete/{cargo_id}")
async def delete_cargo(
    cargo_id: int,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo or cargo.department_id != user.department_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Груз не найден")

    try:
        session.delete(cargo)
        session.commit()
        return JSONResponse(content={"message": "Successfully deleted"}, status_code=status.HTTP_200_OK)
    except Exception:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка базы данных при удалении")


@router.get("/edit/{passenger_id}", response_class=HTMLResponse)
async def edit_form(
    request: Request,
    passenger_id:int,
    session: SessionDep, 
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
    ):
    passenger = session.query(Passenger).filter(Passenger.id==passenger_id).first()
    departments = session.query(Department).all()
    # flight_routes = session.query(FlightRoute).all()
    airports = session.query(Airport).all() 
    return templates.TemplateResponse(request=request, name="transport_dispatcher/edit.html", context={
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
    gtu_relation:GTURelation = Form(...),
    # department_id:int = Form(...),
    application_id: str = Form(...),

    # notes:str = Form(...),
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
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
    passenger.gtu_relation=gtu_relation
    passenger.department_id = user.department_id
    passenger.application_id = application_id
    # passenger.notes=notes

    session.commit()
    return RedirectResponse(url="/transport_dispatcher/", status_code=303)


@router.get("/search-passengers", response_class=JSONResponse)
async def search_passengers(
    query: str,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    """Поиск пассажиров по ФИО, паспорту или дате рождения. Возвращает уникальные комбинации."""
    if not query or len(query.strip()) < 2:
        return JSONResponse(content={"passengers": []})
    
    query_lower = query.lower().strip()
    
    # Ищем пассажиров, созданных текущим пользователем
    passengers = session.query(Passenger).filter(
        Passenger.created_by == user.id
    ).all()
    
    # Фильтруем по совпадению ФИО, паспорта или даты рождения
    # Используем словарь для удаления дубликатов по паспорту и филиалу
    seen = set()
    matching_passengers = []
    
    for passenger in passengers:
        fullname_match = query_lower in passenger.fullname.lower()
        passport_match = query in str(passenger.passport)
        birthdate_match = query in str(passenger.birthdate)
        
        if fullname_match or passport_match or birthdate_match:
            # Ключ для уникальности: паспорт + филиал
            unique_key = (passenger.passport, passenger.department_id)
            
            if unique_key not in seen:
                seen.add(unique_key)
                matching_passengers.append({
                    "fullname": passenger.fullname,
                    "passport": passenger.passport,
                    "birthdate": str(passenger.birthdate),
                    "gender": passenger.gender.value,
                    "department_id": passenger.department_id,
                })
    
    return JSONResponse(content={"passengers": matching_passengers[:10]})  # Лимит 10 результатов


@router.delete("/delete/{passenger_id}")
async def delete_passenger(
    passenger_id: int, 
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    passenger = session.get(Passenger, passenger_id)
    
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Пассажир с ID {passenger_id} не найден"
        )
    
    try:
        session.delete(passenger)
        session.commit()
        
        return JSONResponse(
            content={"message": "Successfully deleted"}, 
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Ошибка базы данных при удалении"
        )



