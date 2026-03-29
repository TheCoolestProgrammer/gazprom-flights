from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.models.passenger_flight import PassengerFlight
from src.models.flights import Flight
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender 
from src.models.department import Department

router = APIRouter(prefix="/dispatcher", tags=["dispatcher"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER))
    ):
    flights = session.query(PassengerFlight).all()
    requests = session.query(Passenger).order_by(Passenger.request_date.desc()).all()
    return templates.TemplateResponse(request=request, name="dispatcher/dashboard.html", context={
        "user": user,
        "requests": requests,
        "flights":flights
    })

@router.get("/create/{passenger_id}", response_class=HTMLResponse)
async def create_view(
    request: Request,
    session: SessionDep,
    passenger_id:int,
    user: User = Depends(RoleChecker(Role.DISPATCHER))
    ):
    flights = session.query(Flight).all()
    passenger = session.get(Passenger, passenger_id)
    return templates.TemplateResponse(request=request, name="dispatcher/create.html", context={
        "flights":flights,
        "passenger":passenger
    })


@router.post("/create/{passenger_id}", response_class=HTMLResponse)
async def create_post(
    session: SessionDep,
    passenger_id:int,
    flight_id:int = Form(...),
    place:str=Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER))
    ):
    pf = PassengerFlight(
        flight_id=flight_id,
        passenger_id=passenger_id,
        place=place
    )
    session.add(pf)
    session.commit()
    return RedirectResponse(url="/dispatcher/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/get_places/{flight_id}")
async def get_places(
    flight_id:int,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER))
):
    occupied = session.query(PassengerFlight.place).filter(PassengerFlight.flight_id==flight_id).all()
    return [item[0] for item in occupied]