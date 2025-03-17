from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.database import Base, engine
from api.routes import auth
from api.routes.v1 import groups, expenses, invitations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    yield
    # Shutdown logic (if any)


# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router, prefix="/auth")

app.include_router(groups.router, prefix="/v1")
app.include_router(invitations.router, prefix="/v1")
app.include_router(expenses.router, prefix="/v1")
