from fastapi import Depends, APIRouter, HTTPException, status
from database.database import get_db
from pydantic import BaseModel
import models.models as models
from sqlalchemy.orm import Session
from routers.auth import get_current_user, get_user_exception, get_user_not_found_exception, get_role_exception, bcrypt_context

router = APIRouter(prefix="/api/v1/services",
                   tags=["Services"])


class CreateService(BaseModel):
    name: str
    family: str
    is_active: bool


@router.post("/register")
def create_service(new_service: CreateService, current_user: dict = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    service_model = models.Services()
    service_model.name = new_service.name
    service_model.family = new_service.family

    db.add(service_model)
    db.commit()

    return new_service


@router.get("/")
def get_all_services(db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    return db.query(models.Services).all()


@router.get("/{service_id}")
def get_service(service_id: int, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    service = db.query(models.Services).filter(
        models.Services.id == service_id).first()

    if not service:
        raise get_service_not_found_exception()

    return service


@router.get("/family/{family}")
def get_services_by_family(family: str, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    return db.query(models.Services).filter(models.Services.family == family).all()


@router.put("/{service_id}")
def update_service(service_id: int, updated_service: CreateService, db=Depends(get_db),
                   current_user: dict = Depends(get_current_user)):

    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    service = db.query(models.Services).filter(
        models.Services.id == service_id).first()

    if not service:
        raise get_service_not_found_exception()

    service.name = updated_service.name
    service.family = updated_service.family
    service.is_active = updated_service.is_active

    db.add(service)
    db.commit()

    return updated_service


@router.get("/users/{user_id}")
def get_services_by_user(user_id: int, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] == "user" and user_id != current_user["id"]:
        raise get_role_exception()

    services_by_user = db.query(models.Permissions).filter(
        models.Permissions.user_id == user_id).all()

    if not services_by_user:
        raise get_user_data_not_found_exception()

    return services_by_user


# exceptions
def get_service_not_found_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Service not found"
    )
    return credentials_exception


def get_user_data_not_found_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No data found for the specified user"
    )
    return credentials_exception
