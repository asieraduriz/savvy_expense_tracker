from fastapi import FastAPI
from backend.models.base import Base
from backend.routes import auth
from backend.database import engine

app = FastAPI()
app.include_router(auth.router, prefix='/auth')

Base.metadata.drop_all(engine)
Base.metadata.create_all(bind=engine)
