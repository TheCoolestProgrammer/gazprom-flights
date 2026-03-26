from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender 
from src.models.department import Department

router = APIRouter(prefix="/transport_dispatcher", tags=["transport_dispatcher"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
    ):
    
    # Получаем все заявки
    requests = session.query(Passenger).order_by(Passenger.request_date.desc()).all()
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
    departments = session.query(Department).all()
    return templates.TemplateResponse(request=request, name="transport_dispatcher/create.html", context={
        "user": user,
        "departments": departments
    })

@router.post("/create")
async def create_request(
    request: Request,
    session: SessionDep,
    fullname: str = Form(...),
    passport: int = Form(...),
    department_id: int = Form(...),
    birthdate: str = Form(...),
    gender: Gender = Form(...),
    trip_purpose: str = Form(...),
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    new_passenger = Passenger(
        fullname=fullname,
        passport=passport,
        department_id=department_id,
        birthdate=birthdate, # Нужна конвертация в date объект
        gender=gender,
        trip_purpose=trip_purpose,
        status=RequestStatus.PENDING,
        created_by=user.id
    )
    session.add(new_passenger)
    session.commit()
    return RedirectResponse(url="/transport_dispatcher/", status_code=303)


@router.get("/edit/{passenger_id}", response_class=HTMLResponse)
async def edit_form(
    request: Request,
    passenger_id:int,
    session: SessionDep, 
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
    ):
    passenger = session.query(Passenger).filter(Passenger.id==passenger_id).first()
    departments = session.query(Department).all()
    return templates.TemplateResponse(request=request, name="transport_dispatcher/edit.html", context={
        "user": user,
        "departments": departments,
        "passenger":passenger
    })

@router.post("/edit/{passenger_id}")
async def edit_request(
    request: Request,
    session: SessionDep,
    passenger_id:int,
    fullname: str = Form(...),
    passport: int = Form(...),
    department_id: int = Form(...),
    birthdate: str = Form(...),
    gender: Gender = Form(...),
    trip_purpose: str = Form(...),
    user: User = Depends(RoleChecker(Role.TRANSPORT_DISPATHER))
):
    passenger = session.get(Passenger, passenger_id)
    
    passenger.fullname=fullname
    passenger.passport=passport
    passenger.department_id=department_id
    passenger.birthdate=birthdate # Нужна конвертация в date объект
    passenger.gender=gender
    passenger.trip_purpose=trip_purpose
    passenger.status=RequestStatus.PENDING
    passenger.created_by=user.id

    session.commit()
    return RedirectResponse(url="/transport_dispatcher/", status_code=303)


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



