from fastapi import FastAPI
from backend.models.base import Base
from backend.routes import auth, v1
from backend.database import engine

app = FastAPI()
app.include_router(auth.router, prefix='/auth')
app.include_router(v1.router, prefix='/v1')

# Base.metadata.drop_all(engine)
Base.metadata.create_all(bind=engine)
