from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database.init_db import init_db
from app.routers import predictions, categories, users

app = FastAPI()

app.include_router(predictions.router)
app.include_router(categories.router)
app.include_router(users.router)

templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def on_startup():
    await init_db()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
@app.get("/new")
async def new_prediction(request: Request):
    return templates.TemplateResponse("new_prediction.html", {"request": request})
@app.get("/manage-categories")
async def manage_categories(request: Request):
    return templates.TemplateResponse("manage_categories.html", {"request": request})
@app.get("/manage-users")
async def manage_users(request: Request):
    return templates.TemplateResponse("manage_users.html", {"request": request})

@app.get("/stats")
async def stats(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})

@app.get("/history")
async def history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})
