from fastapi import FastAPI, Request
import models
from database import engine
from routers import auth, todos, admin
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette import status

app=FastAPI()

models.Base.metadata.create_all(bind=engine)


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def test(request: Request):
    return RedirectResponse(url="/todos/todo-page",status_code=status.HTTP_302_FOUND)

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)