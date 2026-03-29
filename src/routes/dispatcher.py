from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
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
    requests = session.query(Passenger).order_by(Passenger.request_date.desc()).all()
    return templates.TemplateResponse(request=request, name="dispatcher/dashboard.html", context={
        "user": user,
        "requests": requests
    })