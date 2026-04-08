from fastapi import APIRouter, Body, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
# from src.models.flight_route import FlightRoute
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender,TripPurpose, GTURelation
from src.models.department import Department

router = APIRouter(prefix="/main_dispatcher", tags=["main_dispatcher"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DISPATCHER_DIRECTOR))
    ):
    requests = session.query(Passenger).filter(Passenger.department_director_status==RequestStatus.CONFIRMED).order_by(Passenger.request_date.desc()).all()
    return templates.TemplateResponse(request=request, name="main_dispatcher/dashboard.html", context={
        "user": user,
        "requests": requests,
        "Status":RequestStatus
    })


@router.get("/edit/{passenger_id}", response_class=HTMLResponse)
async def edit_form(
    request: Request,
    passenger_id:int,
    session: SessionDep, 
    user: User = Depends(RoleChecker(Role.DISPATCHER_DIRECTOR))
    ):
    passenger = session.query(Passenger).filter(Passenger.id==passenger_id).first()
    departments = session.query(Department).all()
    # flight_routes = session.query(FlightRoute).all()

    return templates.TemplateResponse(request=request, name="main_dispatcher/edit.html", context={
        "user": user,
        "departments": departments,
        "passenger":passenger,
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
    cargo_weight:float = Form(...),
    gtu_relation:GTURelation = Form(...),
    department_id:int = Form(...),
    notes:str = Form(...),
    user: User = Depends(RoleChecker(Role.DISPATCHER_DIRECTOR))
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
    passenger.notes=notes

    session.commit()
    return RedirectResponse(url="/main_dispatcher/", status_code=303)

@router.patch("/change_status/{passenger_id}", response_class=HTMLResponse)
async def change_status(
    request: Request,
    session: SessionDep,
    passenger_id:int,
    request_status:RequestStatus = Body(..., embed=True),
    user: User = Depends(RoleChecker(Role.DISPATCHER_DIRECTOR))
    ):
    passenger = session.get(Passenger,passenger_id)
    
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Пассажир с ID {passenger_id} не найден"
        )
    # try:
    passenger.main_dispatcher_status = request_status
    session.commit()
    
    return JSONResponse(
        content={"message": "Successfully changed"}, 
        status_code=status.HTTP_200_OK
    )
