from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.database import create_db_and_tables
from api.routes import auth
from api.routes.v1 import groups, expenses

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    create_db_and_tables()
    yield
    # Shutdown logic (if any)

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router, prefix="/auth")

app.include_router(groups.router, prefix="/v1")
app.include_router(expenses.router, prefix="/v1")
