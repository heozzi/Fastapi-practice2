import sys
sys.path.append("..")

from fastapi import Depends,APIRouter,Request,Form
from starlette.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status
import models
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from .auth import get_current_user


router = APIRouter(
    prefix="/todos",
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)

# 템플릿 추가
templates = Jinja2Templates(directory='templates/')

# DB 연결
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get('/')
async def homepage(request : Request,db :Session=Depends(get_db)) :
    # auth코드에 get_current_user는 비동기식 함수 이므로 await 함수설정
    # await 설정 안할 시 get_current_user 작동 안됨
    user = await get_current_user(request,db)

    # user가 로그인이 안되어있다고 판단하여 /auth(로그인페이지)로 전달
    if user is None :
        return RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)

    # 로그인한 유저ID와 Todos의 소유자 ID정보를 매칭하여 가져오기
    db_data = db.query(models.Todos).filter(models.Todos.owner_id == user.id).all()

    # home.html 23줄에 todos로 되어있으므로 반환데이터에 todos 설정
    context = {'request': request,'todos':db_data}
    return templates.TemplateResponse('home.html', context)

# complete True/False 체크
# todo_id를 선언하여 진행
@router.get('/complete/{todo_id}')
async def completepage(request:Request,todo_id:int, db:Session=Depends(get_db)) :
    user = await get_current_user(request, db)
    if user is None :
        return RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)

    db_data = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    # complete값은 Bool로 선언되어 있음
    db_data.complete = not db_data.complete
    db.commit()
    return RedirectResponse('/todos',status_code=status.HTTP_302_FOUND)

@router.get("/edit-todo/{todo_id}")
async def edit_get_page(request:Request,todo_id:int,db:Session=Depends(get_db)) :
    user = await get_current_user(request, db)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    db_data = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    # edit-tod.o.html 참조시 todo라는 변수 사용 중
    context = {'request': request,'todo':db_data}
    return templates.TemplateResponse("edit-todo.html", context)

@router.post("/edit-todo/{todo_id}",response_class=HTMLResponse)
async def edit_post_page(request: Request,todo_id : int,db:Session=Depends(get_db),
                         title:str=Form(...),
                         description:str=Form(...),
                         priority:str=Form(...)) :
    user = await get_current_user(request, db)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    db_data = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    db_data.title = title
    db_data.description = description
    db_data.priority = priority

    db.commit()
    return RedirectResponse('/todos',status_code=status.HTTP_302_FOUND)

@router.get("/delete/{todo_id}")
async def deletepage(request:Request,todo_id:int,db:Session=Depends(get_db)) :
    user = await get_current_user(request, db)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()
    return RedirectResponse('/todos', status_code=status.HTTP_302_FOUND)


@router.get("/add-todo")
async def add_get_page(request:Request,db:Session=Depends(get_db)) :
    user = await get_current_user(request, db)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    context = {'request': request}
    return templates.TemplateResponse("add-todo.html", context)

@router.post("/add-todo",response_class=HTMLResponse)
async def add_get_page(request:Request,db:Session=Depends(get_db),
                        title:str=Form(...),
                         description:str=Form(...),
                         priority:str=Form(...)) :
    user = await get_current_user(request, db)
    if user is None:
        return RedirectResponse('/auth', status_code=status.HTTP_302_FOUND)

    new_todos = models.Todos(
        title = title,
        description = description,
        priority = priority,
        complete = False,
        owner_id = user.id)

    db.add(new_todos)
    db.commit()

    return RedirectResponse('/todos', status_code=status.HTTP_302_FOUND)