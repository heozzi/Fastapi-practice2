import sys
sys.path.append("..")

import models
from .auth import get_current_user
from database import engine, SessionLocal

from typing import Optional
from pydantic import BaseModel, Field
from starlette import status
from sqlalchemy.orm import Session

from fastapi import Depends, APIRouter
from fastapi import Form,Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse


template = Jinja2Templates(directory='./templates/')

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Todo(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(gt=0, lt=6, description="The priority must be between 1-5")
    complete: bool


@router.get('/',response_class=HTMLResponse)
async def loginpage(request: Request,
                    db : Session = Depends(get_db)) :
    user = await get_current_user(request)
    if user is None :
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todolist = db.query(models.Todos).filter(models.Todos.owner_id == user.get('id')).all()
    return_dict = {'request': request,'todos' : todolist,'user' : user}
    return template.TemplateResponse('home.html', return_dict)


@router.get("/add-todo",response_class=HTMLResponse)
async def addgetpage(request: Request) :
    user = await get_current_user(request)
    if user is None :
        return RedirectResponse(url='/auth',status_code=status.HTTP_302_FOUND)
    return_dict = {'request': request,'user':user}
    return template.TemplateResponse('add-todo.html', context=return_dict)

@router.post("/add-todo",response_class=HTMLResponse)
async def addpostpage(request: Request, title: str = Form(...),
                    description: str = Form(...), priority: str = Form(...),
                    db : Session() = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth',status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos(
        title = title,
        description = description,
        priority = priority,
        complete = False,
        owner_id = user.get("id")
    )

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url='/todos',status_code=status.HTTP_302_FOUND)

@router.get("/edit-todo/{todo_id}",response_class=HTMLResponse)
async def editgetpage(request : Request,todo_id :int,db :Session= Depends(get_db)) :
    user = await get_current_user(request)
    if user is None :
        return RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    return_dict = {'request': request, 'user': user,'todo':todo}
    return template.TemplateResponse('edit-todo.html',return_dict)

@router.post("/edit-todo/{todo_id}",response_class=HTMLResponse)
async def editpostpage(request : Request,todo_id : int,
                       title : str = Form(...),
                       description : str = Form(...),
                       priority : int = Form(...),
                       db :Session= Depends(get_db)) :
    user = await get_current_user(request)
    if user is None :
        return RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo.title = title
    todo.description = description
    todo.priority = priority

    db.add(todo)
    db.commit()

    return RedirectResponse(url='/todos',status_code=status.HTTP_302_FOUND)

@router.get("/delete/{todo_id}",response_class=HTMLResponse)
async def deletepage(request : Request, todo_id : int,
                     db : Session = Depends(get_db))  :
    user = await get_current_user(request)
    if user is None :
        return RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id)\
        .filter(models.Todos.owner_id == user.get('id')).first()

    if todo is None :
        return RedirectResponse('/todos',status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()

    return RedirectResponse(url='/todos',status_code=status.HTTP_302_FOUND)


@router.get("/complete/{todo_id}",response_class=HTMLResponse)
async def completepage(request : Request, todo_id : int,
                     db : Session = Depends(get_db))  :
    user = await get_current_user(request)
    if user is None :
        return RedirectResponse('/auth',status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo.complete = not todo.complete
    db.commit()

    return RedirectResponse(url='/todos',status_code=status.HTTP_302_FOUND)

















