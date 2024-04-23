import sys

from jose import JWTError

sys.path.append("..")
from fastapi import APIRouter, Request, Depends, Form, Response, HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from sqlalchemy.orm import Session
from database import engine,SessionLocal
from passlib.context import CryptContext
from datetime import timedelta,datetime,timezone
from pydantic import BaseModel
import models
import jwt


SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGORITHM = "HS256"

# bcrypt 기본 설정
bcrptpw = CryptContext(schemes=['bcrypt'],deprecated='auto')

# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# FASTPAI에서 만든 레퍼런스 코드 존재

# Fastapi Oauth2 패스워드 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix='/auth',
    responses={404: {"description": "Not found"}}
)

templates = Jinja2Templates(directory='templates/')

def get_db() :
    try :
        db = SessionLocal()
        yield db
    finally:
        db.close()

# 패스워드 bcrypt사용하여 hash
def get_passwd_hash(password) :
    return bcrptpw.hash(password)

# 패스워드와 hash된 패스워드 비교
def check_verify_password(password,hashedpw):
    return bcrptpw.verify(password,hashedpw)

# 유저인증 함수
# 유저와 패스워드 동일한지 여부 판단
def authenticate_user(username: str, password: str,db):
    user = db.query(models.Users).filter(models.Users.username == username).first()
    if not user: return None
    if not check_verify_password(password, user.hashed_password):
        return None
    return user

# 액세스 토큰 JWT 인코딩으로 생성
# time_expire 유효시간 설정
# 시간 지날시 jwt.exceptions.ExpiredSignatureError: Signature has expired
def create_access_token(data: dict,time_expire):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + time_expire
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 로그인한 기록이 있다면 쿠키를 확인하여 이상여부 판단

async def get_current_user(request : Request,db) :
    try:
        # 'access_token'은 쿠키이름 가져오기
        token = request.cookies.get('access_token')
        if token is None : return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        password: str = payload.get("password")
        token_data = authenticate_user(username,password,db)
        if token_data is None: return None
        return token_data
    # 시간 에러 발생시 logout 실행
    except jwt.ExpiredSignatureError:
        await logout(request)
        return None

@router.get('/')
async def login_get_page(request:Request) :
    context  = {'request' :request}
    return templates.TemplateResponse('login.html',context)


@router.post('/',response_class=HTMLResponse)
async def login_post_page(request:Request, db : Session=Depends(get_db),
                    email : str = Form(...),password : str = Form(...)) :
    
    # 입력받은 정보가 로그인 문제없는지 체크
    user= authenticate_user(email,password,db)
    if user is None :
        context = {'request': request,'msg':'This user does not exist.'}
        return templates.TemplateResponse('login.html', context)
    # 토큰 생성 및 쿠키설정
    time_expire = timedelta(minutes=15)
    access_token = create_access_token(data={"username": email,
                                             'password':password},
                                       time_expire=time_expire)
    # Redirect로 넘길시 쿠키가 전달되지 않은 상황 발생
    # FAST-API 공식문서에서도 직접반환으로 통해 쿠키생성 가능이라고 적혀있음
    # https://fastapi.tiangolo.com/advanced/response-cookies/
    response = RedirectResponse(url='/todos',status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token",value=access_token,expires=time_expire,httponly=False)
    return response

@router.get('/register')
async def register_get_page(request:Request) :
    context  = {'request' :request}
    return templates.TemplateResponse('register.html',context)

@router.post('/register',response_class=HTMLResponse)
async def register_post_page(request:Request,db : Session=Depends(get_db),
                             email: str = Form(...), username: str = Form(...),
                             firstname:str=Form(...),lastname:str=Form(...),
                             password:str=Form(...),password2=Form(...)) :

    if password!=password2 :
        context  = {'request' :request,'msg':'Password mismatch'}
        return templates.TemplateResponse('register.html',context)

    validata= db.query(models.Users).filter(models.Users.email==email).first()
    validata2 = db.query(models.Users).filter(models.Users.username==username).first()
    if validata or validata2 :
        context = {'request': request, 'msg': 'Duplicate ID or email.'}
        return templates.TemplateResponse('register.html', context)
    newuser= models.Users(
        email = email,
        username=username,
        first_name=firstname,
        last_name=lastname,
        hashed_password=get_passwd_hash(password),
        is_active=False
    )
    db.add(newuser)
    db.commit()

    return RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)

# 로그아웃 기능
# 쿠키는 초기화가 되지 않음 하지만 기능적으로 문제없이 작동
@router.get('/logout')
async def logout(request:Request) :
    request.cookies.clear()
    response = RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)
    response.delete_cookie('access_token')
    return response