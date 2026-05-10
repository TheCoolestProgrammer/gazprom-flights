from fastapi import APIRouter, Body, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender
from src.models.cargo import Cargo
from src.models.department import Department
from src.templates_config import templates

router = APIRouter(prefix="/department_director", tags=["department_director"])


from fastapi import APIRouter, Body, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender
from src.models.department import Department
from sqlalchemy import case, cast, String
from sqlalchemy.orm import aliased
from src.models.airport import Airport
from datetime import datetime
from typing import Optional
from fastapi import Query

router = APIRouter(prefix="/department_director", tags=["department_director"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DEPARTMENT_DEIRECTOR)),
    # Параметры фильтрации
    planning_date: Optional[str] = Query(None, description="Желаемая дата"),
    flight_from: Optional[str] = Query(None, description="Откуда"),
    flight_to: Optional[str] = Query(None, description="Куда"),
    fullname: Optional[str] = Query(None, description="ФИО"),
    passport: Optional[str] = Query(None, description="Паспорт"),
):
    # Базовый запрос заявок
    query = session.query(Passenger).filter(Passenger.department_id == user.department_id)
    airport_from = aliased(Airport)
    airport_to = aliased(Airport)

    # Применяем фильтры
    if planning_date:
        try:
            planning_date_obj = datetime.strptime(planning_date, "%Y-%m-%d").date()
            query = query.filter(Passenger.planning_date == planning_date_obj)
        except ValueError:
            pass  # Игнорируем неверный формат даты
    
    if flight_from:
        query = query.join(airport_from, Passenger.flight_from).filter(airport_from.name == flight_from)

    if flight_to:
        query = query.join(airport_to, Passenger.flight_to).filter(airport_to.name == flight_to)

    if fullname:
        query = query.filter(Passenger.fullname.ilike(f"%{fullname}%"))

    if passport:
        query = query.filter(cast(Passenger.passport, String).ilike(f"%{passport}%"))

    # Сортируем: сначала рассматриваемые (PENDING), потом рассмотренные (CONFIRMED, REJECTED)
    # Используем case для кастомной сортировки
    status_order = case(
        (Passenger.department_director_status == RequestStatus.PENDING, 1),
        (Passenger.department_director_status == RequestStatus.CONFIRMED, 2),
        (Passenger.department_director_status == RequestStatus.REJECTED, 3),
        else_=4
    )
    requests = query.order_by(status_order, Passenger.request_date.desc()).all()
    
    # Получаем уникальные значения для фильтров
    all_requests = session.query(Passenger).filter(Passenger.department_id == user.department_id).all()
    
    unique_cities_from = set()
    unique_cities_to = set()
    
    for req in all_requests:
        if req.flight_from:
            unique_cities_from.add(req.flight_from.name)
        if req.flight_to:
            unique_cities_to.add(req.flight_to.name)
    
    return templates.TemplateResponse(request=request, name="department_director/dashboard.html", context={
        "user": user,
        "requests": requests,
        "Status": RequestStatus,
        "filters": {
            "planning_date": planning_date,
            "flight_from": flight_from,
            "flight_to": flight_to,
            "fullname": fullname,
            "passport": passport,
        },
        "unique_cities_from": sorted(unique_cities_from),
        "unique_cities_to": sorted(unique_cities_to),
    })


@router.get("/cargo", response_class=HTMLResponse)
async def cargo_dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DEPARTMENT_DEIRECTOR)),
    planning_date: Optional[str] = Query(None, description="Желаемая дата"),
    flight_from: Optional[str] = Query(None, description="Откуда"),
    flight_to: Optional[str] = Query(None, description="Куда")
):
    query = session.query(Cargo).filter(Cargo.department_id == user.department_id)
    airport_from = aliased(Airport)
    airport_to = aliased(Airport)

    if planning_date:
        try:
            planning_date_obj = datetime.strptime(planning_date, "%Y-%m-%d").date()
            query = query.filter(Cargo.planning_date == planning_date_obj)
        except ValueError:
            pass

    if flight_from:
        query = query.join(airport_from, Cargo.flight_from).filter(airport_from.name == flight_from)

    if flight_to:
        query = query.join(airport_to, Cargo.flight_to).filter(airport_to.name == flight_to)

    status_order = case(
        (Cargo.department_director_status == RequestStatus.PENDING, 1),
        (Cargo.department_director_status == RequestStatus.CONFIRMED, 2),
        (Cargo.department_director_status == RequestStatus.SOVP, 3),
        (Cargo.department_director_status == RequestStatus.REJECTED, 4),
        else_=5
    )
    cargo_requests = query.order_by(status_order, Cargo.request_date.desc()).all()

    all_requests = session.query(Cargo).filter(Cargo.department_id == user.department_id).all()
    unique_cities_from = set()
    unique_cities_to = set()

    for req in all_requests:
        if req.flight_from:
            unique_cities_from.add(req.flight_from.name)
        if req.flight_to:
            unique_cities_to.add(req.flight_to.name)

    return templates.TemplateResponse(request=request, name="department_director/cargo_dashboard.html", context={
        "user": user,
        "cargo_requests": cargo_requests,
        "Status": RequestStatus,
        "filters": {
            "planning_date": planning_date,
            "flight_from": flight_from,
            "flight_to": flight_to,
        },
        "unique_cities_from": sorted(unique_cities_from),
        "unique_cities_to": sorted(unique_cities_to),
    })


@router.post("/cargo/change_status_batch")
async def change_cargo_status_batch(
    session: SessionDep,
    selected_ids: list[int] = Form(...),
    action: str = Form(...),
    user: User = Depends(RoleChecker(Role.DEPARTMENT_DEIRECTOR))
):
    new_status = RequestStatus.CONFIRMED if action == "approved" else RequestStatus.REJECTED

    for cargo_id in selected_ids:
        cargo = session.get(Cargo, cargo_id)
        if cargo and cargo.department_id == user.department_id:
            cargo.department_director_status = new_status

    session.commit()
    return RedirectResponse(url="/department_director/cargo", status_code=303)


@router.patch("/cargo/change_status/{cargo_id}", response_class=HTMLResponse)
async def change_cargo_status(
    request: Request,
    session: SessionDep,
    cargo_id: int,
    request_status: RequestStatus = Body(..., embed=True),
    user: User = Depends(RoleChecker(Role.DEPARTMENT_DEIRECTOR))
):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Груз с ID {cargo_id} не найден"
        )

    cargo.department_director_status = request_status
    session.commit()

    return JSONResponse(
        content={"message": "Successfully changed"},
        status_code=status.HTTP_200_OK
    )


@router.post("/change_status_batch")
async def change_status_batch(
    session: SessionDep,
    selected_ids: list[int] = Form(...),
    action: str = Form(...),
    user: User = Depends(RoleChecker(Role.DEPARTMENT_DEIRECTOR))
):
    """Массовое изменение статуса заявок"""
    # Определяем статус на основе действия
    new_status = RequestStatus.CONFIRMED if action == "approved" else RequestStatus.REJECTED
    
    # Обновляем статус для всех выбранных заявок
    for passenger_id in selected_ids:
        passenger = session.get(Passenger, passenger_id)
        if passenger and passenger.department_id == user.department_id:
            passenger.department_director_status = new_status
    
    session.commit()
    return RedirectResponse(url="/department_director", status_code=303)


@router.patch("/change_status/{passenger_id}", response_class=HTMLResponse)
async def change_status(
    request: Request,
    session: SessionDep,
    passenger_id:int,
    request_status:RequestStatus = Body(..., embed=True),
    user: User = Depends(RoleChecker(Role.DEPARTMENT_DEIRECTOR))
    ):
    passenger = session.get(Passenger,passenger_id)
    
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Пассажир с ID {passenger_id} не найден"
        )
    # try:
    passenger.department_director_status = request_status
    session.commit()
    
    return JSONResponse(
        content={"message": "Successfully changed"}, 
        status_code=status.HTTP_200_OK
    )
    # except Exception as e:
    #     session.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
    #         detail="Ошибка базы данных при удалении"
    #     )

