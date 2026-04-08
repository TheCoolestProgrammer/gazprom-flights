from fastapi import APIRouter, Body, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender
from src.models.department import Department
from src.models.passenger import RequestStatus

router = APIRouter(prefix="/department_director", tags=["department_director"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: SessionDep,
    user: User = Depends(RoleChecker(Role.DEPARTMENT_DEIRECTOR))
    ):
    # Получаем все заявки
    requests = session.query(Passenger).filter(Passenger.department_id==user.department_id).order_by(Passenger.request_date.desc()).all()
    return templates.TemplateResponse(request=request, name="department_director/dashboard.html", context={
        "user": user,
        "requests": requests,
        "Status":RequestStatus
    })



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

