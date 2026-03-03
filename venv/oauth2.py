from passlib.context import CryptContext
from jose import jwt,JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from pydantic_settings import BaseSettings
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import datetime, timedelta

class Settings(BaseSettings):
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int

    class Config:
        env_file = ".env"
    
settings = Settings()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow()+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated = "auto")

def get_password_hashed(password:str):
    return pwd_context.hash(password)
def verify_password(plain_password:str, hashed_password:str):
    return pwd_context.verify(plain_password, hashed_password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_student(
        token:str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        student_id:str = payload.get("student_id")
        if student_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    student = db.query(models.Student).filter(models.Student.id == student_id).first()

    if student is None:
        raise credentials_exception
    return student

def get_current_teacher(
        token:str=Depends(oauth2_scheme),
        db:Session=Depends(get_db)
):
    credentials_exception=HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate Credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
        teacher_id:str = payload.get("teacher_id")
        if teacher_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if teacher is None:
        raise credentials_exception
    return teacher
    