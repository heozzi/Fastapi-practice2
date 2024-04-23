from fastapi import FastAPI
import models
from database import engine
from routers import auth, todos
from starlette.staticfiles import StaticFiles

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

# static 파일을 추가 안할시 에러 발생
# starlette.routing.NoMatchFound: No route exists for name "static" and params "path".
# https://fastapi.tiangolo.com/tutorial/static-files/
# 아래 코드 추가시 문제 해결
app.mount('/static',StaticFiles(directory='static'),name='static')

app.include_router(auth.router)
app.include_router(todos.router)

