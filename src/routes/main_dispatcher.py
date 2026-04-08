from fastapi import APIRouter, Body, HTTPException, Request, Depends, Form, status,UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.crud.flight import create_flights_bulk
from src.database import SessionDep
from src.dependencies import get_current_user, RoleChecker
# from src.models.flight_route import FlightRoute
from src.models.user import User, Role
from src.models.passenger import Passenger, RequestStatus,Gender,TripPurpose, GTURelation
from src.models.department import Department
from src.schemas.flight import FlightCreate, FlightResponse, FlightParseResponse
from src.parsers.docs_parser import parse_flight_docx

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


@router.post("/upload-docx", response_model=FlightParseResponse)
async def upload_flights_docx(
    db: SessionDep,
    file: UploadFile = File(..., description="DOCX файл с заявкой на полёты")
):
    """
    Загружает DOCX файл с заявкой на выполнение полетов,
    парсит его и сохраняет данные в базу данных.
    """
    # Проверка типа файла
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла. Ожидается файл с расширением .docx"
        )
    
    try:
        # Чтение содержимого файла
        file_content = await file.read()
        
        # Парсинг документа
        parsed_data = parse_flight_docx(file_content)
        
        if not parsed_data["departure_date"]:
            raise HTTPException(
                status_code=400,
                detail="Не удалось найти дату выполнения полётов в документе"
            )
        
        if not parsed_data["flights"]:
            raise HTTPException(
                status_code=400,
                detail="Не удалось найти рейсы в документе"
            )
        
        # Подготовка данных для сохранения
        flights_to_create = []
        for flight_data in parsed_data["flights"]:
            flight_create = FlightCreate(
                aircraft_type=flight_data["aircraft_type"],
                flight_number=flight_data["flight_number"],
                departure_date=parsed_data["departure_date"],
                departure_time=flight_data["departure_time"],
                place_number=flight_data["place_number"],
                route=flight_data["route"]
            )
            flights_to_create.append(flight_create)
        
        # Сохранение в БД
        saved_flights = create_flights_bulk(db, flights_to_create)
        
        # Преобразование в response schema
        flights_response = [
            FlightResponse(
                id=flight.id,
                aircraft_type=flight.aircraft_type,
                flight_number=flight.flight_number,
                departure_date=flight.departure_date,
                departure_time=flight.departure_time,
                place_number=flight.place_number,
                route=flight.route
            )
            for flight in saved_flights
        ]
        
        return FlightParseResponse(
            status="success",
            message=f"Успешно обработано {len(saved_flights)} рейсов",
            flights_parsed=len(saved_flights),
            flights_saved=flights_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"Ошибка при обработке файла: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера при обработке файла: {str(e)}"
        )
