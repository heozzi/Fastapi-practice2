import sys
sys.path.append("..")

import models
from database import SessionLocal, engine

from jose import jwt, JWTError
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status, APIRouter,Request,Form,Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from starlette.responses import RedirectResponse

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

template = Jinja2Templates(directory='./templates/')


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users)\
        .filter(models.Users.username == username)\
        .first()

    if not user: return False
    if not verify_password(password, user.hashed_password):  return False
    return user


def create_access_token(username: str, user_id: int,
                        expires_delta: Optional[timedelta] = None):

    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request : Request):
    try:
        token = request.cookies.get("access_token")
        if token is None: return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            logout(request)
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=404, detail="Not found")



@router.post("/token")
async def login_for_access_token(response : Response,
                                 form_data : OAuth2PasswordRequestForm = Depends(),
                                 db : Session=Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user: return False

    token_expires = timedelta(minutes=60)
    token = create_access_token(user.username,
                                user.id,
                                expires_delta=token_expires)
    response.set_cookie(key="access_token", value=token, httponly=True)

    return True

@router.get('/')
async def loginpage(request: Request) :
    return_dict = {'request': request}
    return template.TemplateResponse('login.html', context=return_dict)

@router.post('/',response_class=HTMLResponse)
async def loginpage(request: Request,db : Session = Depends(get_db)) :
    try :
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response=response,form_data=form, db=db)

        if not validate_user_cookie:
            msg = "Incorrect Username or Password"
            return template.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return template.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.get("/logout")
async def logout(request: Request):
    msg = "Logout Successful"
    response = template.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response


@router.get('/register')
async def registerpage(request: Request) :
    return_dict = {'request': request}
    return template.TemplateResponse('register.html', context=return_dict)

@router.post('/register',response_class=HTMLResponse)
async def registerpage(request: Request,db : Session = Depends(get_db),
                       email:str = Form(...),username:str = Form(...),
                       firstname:str = Form(...),lastname:str = Form(...),
                       password:str = Form(...),password2:str = Form(...)) :
    validation1 = db.query(models.Users).filter(models.Users.username == username).first()
    validation2 = db.query(models.Users).filter(models.Users.email == email).first()
    if password != password2 or validation1 is not None or validation2 is not None:

        msg = "Invalid registration request"
        return template.TemplateResponse("register.html", {"request": request, "msg": msg})

    hash_pwd = get_password_hash(password)
    newuser = models.Users(
        email =email,
        username = username,
        first_name = firstname,
        last_name = lastname,
        hashed_password = hash_pwd,
        is_active=True
    )
    db.add(newuser)
    db.commit()
    return_dict = {'request': request,'msg' : "User successfully created"}
    return template.TemplateResponse('login.html', return_dict)


#Exceptions
def get_user_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception


def token_exception():
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return token_exception_response












