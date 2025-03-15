from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = 'postgresql://admin:admin@localhost:5432/savvy'

engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)