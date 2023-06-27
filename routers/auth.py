from fastapi import Depends, HTTPException, status, APIRouter, Response
from typing import Optional, List
import models.models as models
from security.oauth2 import OAuth2PasswordBearerWithCookie
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database.database import get_db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt, JWTError

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
EXPIRATION_MINUTES = int(os.environ["EXPIRATION_MINUTES"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/login")
# oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter(prefix="/api/v1/auth",
                   tags=["Authentication"])


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users).filter(
        models.Users.username == username).first()
    if not user or not verify_password(password, user.password):
        return False
    return user


def create_access_token(username: str, user_id: int, user_role: str, subscription: str,
                        expires_delta: Optional[timedelta] = None, permissions_list: List[int] = None):
    encode = {"sub": username, "id": user_id, "role": user_role,
              "subscription": subscription, "permissions": permissions_list}
    encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    old_token = db.query(models.InvalidJWT).filter(
        models.InvalidJWT.token == token).first()
    if old_token:
        raise token_invalid_exception()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise get_user_exception()
    username: str = payload.get("sub")
    user_id: int = payload.get("id")
    user_role: str = payload.get("role")
    user_permissions = payload.get("permissions")
    user_subscription = payload.get("subscription")
    if not (username or user_id or user_role):
        raise get_user_exception()
    return {"username": username, "id": user_id, "role": user_role, "permissions": user_permissions, "subscription": user_subscription}


@router.post("/login")
def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise token_exception()
    if not user.is_active:
        raise get_user_inactivate_exception()
    inactive_services = [s.id for s in db.query(
        models.Services).filter(models.Services.is_active == False).all()]
    permissions_list = [p.service_id for p in db.query(models.Permissions).filter(
        models.Permissions.user_id == user.id).all() if p.service_id not in inactive_services]
    token_expires = timedelta(minutes=EXPIRATION_MINUTES)
    token = create_access_token(
        user.username, user.id, user.role, user.subscription, token_expires, permissions_list)
    response.set_cookie(
        key="access_token", value=f"Bearer {token}", httponly=True, secure=False, samesite="lax")
    return {"access_token": token, "token_type": "Bearer"}


@router.post("/logout")
def logout(response: Response, token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    response.delete_cookie("access_token")

    token_model = models.InvalidJWT()
    token_model.token = token

    db.add(token_model)
    db.commit()

    return {"detail": "Logout successful"}


# exceptions
def get_user_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    return credentials_exception


def get_user_inactivate_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your user is deactivated"
    )
    return credentials_exception


def get_user_not_found_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
    return credentials_exception


def get_role_exception():
    role_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this route"
    )
    return role_exception


def get_permissions_exception():
    role_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this service"
    )
    return role_exception


def token_exception():
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )
    return token_exception_response


def token_invalid_exception():
    token_invalid_response = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid token, please generate a new token"
    )
    return token_invalid_response
