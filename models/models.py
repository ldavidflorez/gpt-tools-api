import datetime
from sqlalchemy import Column, Enum, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(16), unique=True, index=True)
    password = Column(String(200))
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    role = Column(Enum("admin", "user"), default="user")
    subscription = Column(Enum("standard", "premium"), default="standard")
    is_active = Column(Boolean, default=True)

    tracking = relationship("Tracking", back_populates="user")


class Permissions(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    available_tokens = Column(Integer, default=0)


class Services(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    family = Column(String(100))
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

    tracking = relationship("Tracking", back_populates="service")


class Tracking(Base):
    __tablename__ = "tracking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    insertion_date = Column(DateTime, default=datetime.datetime.utcnow)
    consumed_tokens = Column(Integer)

    user = relationship("Users", back_populates="tracking")
    service = relationship("Services", back_populates="tracking")


class InvalidJWT(Base):
    __tablename__ = "invalid_jwt"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500))
    insertion_date = Column(DateTime, default=datetime.datetime.utcnow)
