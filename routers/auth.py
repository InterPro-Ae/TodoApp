from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from pydantic import BaseModel
from models import Users
from passlib.context import CryptContext
from starlette import status
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime,timedelta,timezone
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY='5fb5330a875638e84b2d4f54f9ea2d8ab3420c6b28d7628593d1d94bed5968d0'
ALGORITHM = 'HS256'

bcrypt_context=CryptContext(schemes=['bcrypt'],deprecated='auto')
oauth2_bearer=OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    username:str
    email:str
    first_name:str
    last_name:str
    password:str    
    role:str

class Token(BaseModel):
    access_token:str
    token_type:str

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

templates= Jinja2Templates(directory="templates")

### Pages ###
@router.get("/login-page")
def render_login_page(request:Request):
   return templates.TemplateResponse(
    request=request,
    name="login.html"
)

@router.get("/register-page")
def render_register_page(request:Request):
   return templates.TemplateResponse(
    request=request,
    name="register.html"
)

### Endpoint ###




def authenticate_user(username:str,password:str,db):
    user= db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username:str,user_id:int,role:str,expires_delta:timedelta):

    encode={'sub':username, 'id':user_id, 'role':role}
    expires = datetime.now(timezone.utc)+expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode,SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload=jwt.decode(token, SECRET_KEY,algorithms=[ALGORITHM])
        username:str = payload.get('sub')
        user_id:int = payload.get('id')
        user_role:str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Could not vaildate user')
        return{'username':username, 'id':user_id, 'user_role':user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Could not vaildate user')






@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    try:
        create_user_model = Users(
            email=create_user_request.email,
            username=create_user_request.username,
            first_name=create_user_request.first_name,
            last_name=create_user_request.last_name,
            role=create_user_request.role,
            hashed_password=bcrypt_context.hash(create_user_request.password),
            is_active=True
        )
        db.add(create_user_model)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],
                                 db:db_dependency):
    user = authenticate_user(form_data.username, form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Could not vaildate user')

    token=create_access_token(user.username, user.id,user.role,timedelta(minutes=20))

    return {'access_token':token, 'token_type':'bearer'}


@router.post("/login")
async def login(request: Request, db: db_dependency, username: str = Form(), password: str = Form()):
    """Form-based login that sets cookie and redirects to todo page"""
    user = authenticate_user(username, password, db)

    if not user:
        # Redirect back to login page with error
        return RedirectResponse(url="/auth/login-page?error=Invalid credentials", status_code=status.HTTP_302_FOUND)

    # Create access token
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))

    # Redirect to todo page and set cookie
    response = RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)

    return response