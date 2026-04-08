from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
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
    user: User = Depends(RoleChecker(Role.DISPATCHER))
    ):
    # flights = session.query(Flight).filter(Flight.departure_date>datetime.date.today()).all()
    stmt = select(Flight).where(Flight.departure_date > datetime.date.today())

    # Выполняем и получаем результат
    flights = session.execute(stmt).scalars().all()
    requests = session.query(Passenger).filter(Passenger.done_status!=RequestStatus.CONFIRMED).order_by(Passenger.request_date.desc()).all()
    return templates.TemplateResponse(request=request, name="dispatcher/dashboard.html", context={
        "user": user,
        "requests": requests,
        "flights":flights
    })


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