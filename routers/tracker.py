from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Date, cast
import models.models as models
from database.database import get_db
from routers.auth import get_current_user, get_user_exception, get_role_exception
from typing import Optional
from datetime import date

import os

COST_BY_TOKEN = float(os.environ["COST_BY_TOKEN"])

router = APIRouter(prefix="/api/v1/tracker",
                   tags=["Tracking"])


@router.get("/historical")
async def historical(
        start_date: Optional[date] = None, end_date: Optional[date] = None,
        user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    if user["role"] != "admin":
        raise get_role_exception()

    if start_date and end_date:
        data = db.query(models.Tracking).filter(cast(models.Tracking.insertion_date, Date) <= end_date).filter(
            cast(models.Tracking.insertion_date, Date) >= start_date).all()
    else:
        data = db.query(models.Tracking).all()

    users = {}

    for row in data:
        username = row.user.username
        service_name = row.service.name
        row.username = username
        row.service_name = service_name
        delattr(row, "user")
        delattr(row, "service")
        users[row.user_id] = username

    if not data:
        raise get_user_data_not_found_exception()

    data = [r.__dict__ for r in data]
    for d in data:
        d["price"] = round(d["consumed_tokens"]*COST_BY_TOKEN, 2)

    users_id = list(set(d["user_id"] for d in data))
    summary = []
    for u in users_id:
        user_data = list(filter(lambda d: d["user_id"] == u, data))
        consumed_tokens = round(
            sum(r["consumed_tokens"] for r in user_data), 2)
        consumed_balance = round(sum(r["price"] for r in user_data), 2)
        summary.append(
            {"user_id": u, "username": users[u], "consumed_tokens": consumed_tokens, "consumed_balance": consumed_balance})

    return {"historical": data, "summary": summary}


@router.get("/historical/user/{user_id}")
async def historical_by_user(user_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db),
                             start_date: Optional[date] = None, end_date: Optional[date] = None):
    if user is None:
        raise get_user_exception()

    if user["role"] == "user" and user_id != user["id"]:
        raise get_role_exception()

    if start_date and end_date:
        data = db.query(models.Tracking).filter(models.Tracking.user_id == user_id).filter(cast(
            models.Tracking.insertion_date, Date) <= end_date).filter(cast(models.Tracking.insertion_date, Date) >= start_date).all()
    else:
        data = db.query(models.Tracking).filter(
            models.Tracking.user_id == user_id).all()

    for row in data:
        username = row.user.username
        service_name = row.service.name
        row.username = username
        row.service_name = service_name
        delattr(row, "user")
        delattr(row, "service")

    user_permissions = db.query(models.Permissions).filter(
        models.Permissions.user_id == user_id).all()

    if not data and not user_permissions:
        raise get_user_data_not_found_exception()

    data = [r.__dict__ for r in data]
    for d in data:
        d["price"] = round(d["consumed_tokens"]*COST_BY_TOKEN, 2)

    user_data = list(filter(lambda d: d["user_id"] == user_id, data))
    consumed_tokens = round(
        sum(r["consumed_tokens"] for r in user_data), 2)
    consumed_balance = round(sum(r["price"] for r in user_data), 2)

    if db.query(models.Users).filter(
            models.Users.id == user_id).first().subscription == "standard":
        available_tokens = sum([r.available_tokens for r in user_permissions])
        available_balance = round(available_tokens * COST_BY_TOKEN, 2)
    else:
        available_tokens = None
        available_balance = None

    summary = {"user_id": user_id, "username": username, "consumed_tokens": consumed_tokens,
               "consumed_balance": consumed_balance, "available_tokens": available_tokens, "available_balance": available_balance}

    return {"historical": data, "summary": [summary]}


@router.get("/historical/service/{service_id}")
async def historical_by_service(service_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db),
                                start_date: Optional[date] = None, end_date: Optional[date] = None):
    if user is None:
        raise get_user_exception()

    if user["role"] != "admin":
        raise get_role_exception()

    if start_date and end_date:
        data = db.query(models.Tracking).filter(models.Tracking.service_id == service_id).filter(cast(
            models.Tracking.insertion_date, Date) <= end_date).filter(cast(models.Tracking.insertion_date, Date) >= start_date).all()
    else:
        data = db.query(models.Tracking).filter(
            models.Tracking.service_id == service_id).all()

    if not data:
        raise get_user_data_not_found_exception()

    data = [r.__dict__ for r in data]
    for d in data:
        d["price"] = round(d["consumed_tokens"]*COST_BY_TOKEN, 2)

    consumed_tokens = round(
        sum(r["consumed_tokens"] for r in data), 2)
    consumed_balance = round(sum(r["price"] for r in data), 2)
    summary = {"consumed_tokens": consumed_tokens,
               "consumed_balance": consumed_balance}

    return {"historical": data, "summary": [summary]}


@router.get("/historical/{user_id}/{service_id}")
async def historical_by_user(user_id: int, service_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db),
                             start_date: Optional[date] = None, end_date: Optional[date] = None):
    if user is None:
        raise get_user_exception()

    if user["role"] == "user" and user_id != user["id"]:
        raise get_role_exception()

    if start_date and end_date:
        data = db.query(models.Tracking).filter(models.Tracking.user_id == user_id).filter(models.Tracking.service_id == service_id).filter(
            cast(models.Tracking.insertion_date, Date) <= end_date).filter(cast(models.Tracking.insertion_date, Date) >= start_date).all()
    else:
        data = db.query(models.Tracking).filter(models.Tracking.user_id == user_id).filter(
            models.Tracking.service_id == service_id).all()

    if not data:
        raise get_user_data_not_found_exception()

    data = [r.__dict__ for r in data]
    for d in data:
        d["price"] = round(d["consumed_tokens"]*COST_BY_TOKEN, 2)

    consumed_tokens = round(
        sum(r["consumed_tokens"] for r in data), 2)
    consumed_balance = round(sum(r["price"] for r in data), 2)
    summary = {"user_id": user_id,
               "consumed_tokens": consumed_tokens, "consumed_balance": consumed_balance}

    return {"historical": data, "summary": [summary]}


# exceptions
def get_user_data_not_found_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No data found for the specified user"
    )
    return credentials_exception
