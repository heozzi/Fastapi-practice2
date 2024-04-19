from fastapi import FastAPI
import models
from database import engine
from routers import auth, todos,web
from starlette.staticfiles import StaticFiles

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount('/statc',StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(web.router)
