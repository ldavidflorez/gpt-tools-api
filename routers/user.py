from fastapi import Depends, APIRouter
from database.database import get_db
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import models.models as models
from sqlalchemy.orm import Session
from routers.auth import get_current_user, get_user_exception, get_user_not_found_exception, get_role_exception, bcrypt_context


password_regex = "((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W]).{8,64})"

router = APIRouter(prefix="/api/v1/users",
                   tags=["Users"])


def get_password_hash(password):
    return bcrypt_context.hash(password)


class CreateUser(BaseModel):
    username: str
    password: str = Field(regex=password_regex)
    role: str
    subscription: str
    services: List[int]
    tokens_by_service: List[int]

    @validator('tokens_by_service')
    def tokens_greater_than_zero(cls, v):
        for t in v:
            if t < 0:
                raise ValueError(
                    "service tokens must be greater or equal than zero")
        return v


class UpdateUser(BaseModel):
    username: str
    password: Optional[str] = Field(regex=password_regex)


class UpdateUserAdmin(BaseModel):
    username: str
    password: Optional[str] = Field(regex=password_regex)
    role: str
    subscription: str
    services: List[int]
    tokens_by_service: List[int]
    services_to_delete: Optional[List[int]] = []

    @validator('tokens_by_service')
    def tokens_greater_than_zero(cls, v):
        for t in v:
            if t < 0:
                raise ValueError(
                    "service tokens must be greater or equal than zero")
        return v


@router.post("/register")
def create_user(new_user: CreateUser, current_user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    user_model = models.Users()
    user_model.username = new_user.username
    user_model.password = get_password_hash(new_user.password)
    user_model.role = new_user.role
    user_model.subscription = new_user.subscription

    db.add(user_model)
    db.commit()

    if new_user.subscription == "standard":
        for s, t in zip(new_user.services, new_user.tokens_by_service):
            permissions_model = models.Permissions()
            permissions_model.user_id = user_model.id
            permissions_model.service_id = s
            permissions_model.available_tokens = t

            db.add(permissions_model)
            db.commit()
    else:
        for s in new_user.services:
            permissions_model = models.Permissions()
            permissions_model.user_id = user_model.id
            permissions_model.service_id = s

            db.add(permissions_model)
            db.commit()

    return new_user


@router.get("/")
def get_all_users(db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    users = [{i: u.__dict__[i] for i in u.__dict__ if i != "password"}
             for u in db.query(models.Users).all()]
    return users


@router.get("/myself")
def get_user_information(db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()
    return current_user


@router.get("/{user_id}")
def get_user(user_id: int, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] == "user" and user_id != current_user["id"]:
        raise get_role_exception()

    user = db.query(models.Users).filter(
        models.Users.id == user_id).first()

    if not user:
        raise get_user_not_found_exception()

    return {i: user.__dict__[i] for i in user.__dict__ if i != "password"}


@router.get("/role/{role}")
def get_users_by_role(role: str, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    users = [{i: u.__dict__[i] for i in u.__dict__ if i != "password"}
             for u in db.query(models.Users).filter(models.Users.role == role).all()]
    return users


@router.get("/subscription/{subscription}")
def get_users_by_subscription(subscription: str, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    users = [{i: u.__dict__[i] for i in u.__dict__ if i != "password"}
             for u in db.query(models.Users).filter(models.Users.subscription == subscription).all()]
    return users


@router.put("/as-admin/{user_id}")
def update_user_as_admin(user_id: int, updated_user: UpdateUserAdmin, db=Depends(get_db), current_user: dict = Depends(get_current_user)):

    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if not user:
        raise get_user_not_found_exception()

    user.username = updated_user.username

    if updated_user.password:
        user.password = get_password_hash(updated_user.password)

    user.role = updated_user.role
    user.subscription = updated_user.subscription

    db.add(user)
    db.commit()

    if updated_user.services_to_delete:
        for s in updated_user.services_to_delete:
            db.query(models.Permissions).filter(models.Permissions.user_id == user_id).filter(
                models.Permissions.service_id == s).delete()
            db.commit()

    if user.subscription == "standard":
        for s, t in zip(updated_user.services, updated_user.tokens_by_service):
            old_service = db.query(models.Permissions).filter(
                models.Permissions.user_id == user_id).filter(models.Permissions.service_id == s).first()

            if old_service:
                old_service.available_tokens = t
                db.add(old_service)
                db.commit()

                continue

            permissions_model = models.Permissions()
            permissions_model.user_id = user_id
            permissions_model.service_id = s
            permissions_model.available_tokens = t

            db.add(permissions_model)
            db.commit()
    else:
        for s in updated_user.services:
            old_service = db.query(models.Permissions).filter(
                models.Permissions.user_id == user_id).filter(models.Permissions.service_id == s).first()

            if old_service:
                continue

            permissions_model = models.Permissions()
            permissions_model.user_id = user_id
            permissions_model.service_id = s
            permissions_model.available_tokens = 0

            db.add(permissions_model)
            db.commit()

    return updated_user


@router.put("/as-user/{user_id}")
def update_user_as_user(user_id: int, updated_user: UpdateUser, db=Depends(get_db), current_user: dict = Depends(get_current_user)):

    if current_user is None:
        raise get_user_exception()

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if not user:
        raise get_user_not_found_exception()

    user.username = updated_user.username

    if updated_user.password:
        user.password = get_password_hash(updated_user.password)

    db.add(user)
    db.commit()

    return updated_user


@router.put("/activate/{user_id}")
def activate_user(user_id: int, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if not user:
        raise get_user_not_found_exception()

    user.is_active = 1
    db.commit()

    return {"detail": "User activated successfully"}


@router.put("/deactivate/{user_id}")
def deactivate_user(user_id: int, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise get_user_exception()

    if current_user["role"] != "admin":
        raise get_role_exception()

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if not user:
        raise get_user_not_found_exception()

    user.is_active = 0
    db.commit()

    return {"detail": "User deactivated successfully"}
