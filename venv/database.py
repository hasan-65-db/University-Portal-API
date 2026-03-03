from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url = "sqlite:///./studentsmanager.db"

Engine = create_engine(url, connect_args={"check_same_thread":False})

SessionLocal = sessionmaker(autocommit = False, autoflush= False, bind = Engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()