from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url = "postgresql://user:password@db:5432/course_manager_db"

Engine = create_engine(url)

SessionLocal = sessionmaker(autocommit = False, autoflush= False, bind = Engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()