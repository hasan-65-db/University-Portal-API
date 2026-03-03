from pydantic import BaseModel, EmailStr
from datetime import date

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class StudentResponse(BaseModel):
    id: int
    name: str 
    email: EmailStr 

    class Config:
        from_attributes=True

class CourseCreate(BaseModel):
    title: str
    name: str

class CourseResponse(BaseModel):
    id: int
    title: str
    name: str
    teacher_id: int

    class Config:
        from_attributes=True

class AssignmentCreate(BaseModel):
    title: str
    course_id :int
    description: str
    due_date: date

class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    title: str        
    description: str  
    due_date: date

    class Config:
        from_attributes= True
    
class TeacherCreate(BaseModel):
    name:str
    email:str
    password:str

class TeacherResponse(BaseModel):
    id:int
    name:str

    class Config:
        from_attributes = True

class AnnouncementCreate(BaseModel):
    title:str
    content:str
    teacher_id:int
    course_id:int

class AnnouncementResponse(BaseModel):
    id:int
    title:str
    content: str      
    course_id: int    

    class Config:
        from_attributes = True