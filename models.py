from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True)
    username = Column(String(255), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(50))


    

class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    complete = Column(Boolean, default=False)
    priority = Column(String(10), default="medium")
    owner_id=Column(Integer, ForeignKey("users.id"))
   
