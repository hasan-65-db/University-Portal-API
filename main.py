from fastapi import FastAPI, Depends, HTTPException,status, Response,Query, File, UploadFile
from sqlalchemy.orm import Session
from database import Engine, get_db
import schemas, models, oauth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from fastapi.middleware.cors import CORSMiddleware;
import redis, json
from redis_client import redis_client
from worker import send_registration_email


models.Base.metadata.create_all(bind=Engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.post("/register",response_model=schemas.StudentResponse)
def register_student(
    student: schemas.StudentCreate,
    db:Session=Depends(get_db)
):
    db_stu = db.query(models.Student).filter(models.Student.email==student.email).first()
    if db_stu:
        raise HTTPException(status_code=404,detail="Student already registered")
    hashed_pwd = oauth2.get_password_hashed(student.password)
    new_stu =models.Student(
        name = student.name,
        email = student.email,
        password = hashed_pwd
    )
    db.add(new_stu)
    db.commit()
    db.refresh(new_stu)
    return new_stu

@app.post("/Register/Teacher", response_model=schemas.TeacherCreate)
def register_teacher(
    teacher: schemas.TeacherCreate,
    db:Session=Depends(get_db)
):
    db_teacher = db.query(models.Teacher).filter(models.Teacher.email==teacher.email).first()
    if db_teacher:
        raise HTTPException(status_code=404, detail="Teacher already registered")
    hashed_pwd = oauth2.get_password_hashed(teacher.password)
    new_teacher = models.Teacher(
        name = teacher.name,
        email = teacher.email,
        password = hashed_pwd
    )
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    return new_teacher

@app.post("/login")
def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    rate_key = f"login_attempts_{credentials.username}"
    attempts = redis_client.incr(rate_key)
    if attempts==1:
        redis_client.expire(rate_key,60)
    if attempts>5:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts.Try again after a minute"
        )
    student = db.query(models.Student).filter(models.Student.email == credentials.username).first()
    if student and oauth2.verify_password(credentials.password, student.password):
        redis_client.delete(rate_key)
        token = oauth2.create_access_token(data={"student_id": student.id})
        return {"access_token": token, "token_type": "bearer"}
    
    teacher = db.query(models.Teacher).filter(models.Teacher.email == credentials.username).first()
    if teacher and oauth2.verify_password(credentials.password, teacher.password):
        redis_client.delete(rate_key)
        token = oauth2.create_access_token(data={"teacher_id": teacher.id})
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Invalid Credentials")


@app.get("/Courses",response_model=list[schemas.CourseResponse])
def registered_Courses(
    db:Session=Depends(get_db),
    current_student:models.Student=Depends(oauth2.get_current_student)
):
    cache_key = f"courses_student_{current_student.id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        print("Cache hit!")
        return json.loads(cached_data)
    print("Cache Miss")
    courses = current_student.courses
    course_list = [
        schemas.CourseResponse.model_validate(course).model_dump()
        for course in courses
    ]
    redis_client.setex(
        cache_key,
        300,
        json.dumps(course_list)
    )
    return course_list

    
@app.get("/Assignments",response_model=list[schemas.AssignmentResponse])
def get_assignments(
    db:Session=Depends(get_db),
    current_student:models.Student=Depends(oauth2.get_current_student)    
):
    cache_key = f"assignments_students_{current_student.id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        print("Cache Hit!")
        return json.loads(cached_data)
    print("Cache Miss!")
    assignments = db.query(models.Assignment)\
    .join(models.Course)\
    .join(models.Enrollments)\
    .filter(models.Enrollments.student_id==current_student.id)\
    .distinct()\
    .all()
    assignment_list = [
        schemas.AssignmentResponse.model_validate(assignment).model_dump()
        for assignment in assignments
    ]
    redis_client.setex(
        cache_key,
        300,
        json.dumps(assignment_list)
    )
    return assignment_list
    

@app.get("/Announcements",response_model=list[schemas.AnnouncementResponse])
def Announcements(
    course_id:int,
    db:Session=Depends(get_db),
    current_student:models.Student=Depends(oauth2.get_current_student)
):
    enrollment = db.query(models.Enrollments).filter(models.Enrollments.student_id==current_student.id,
                                                     models.Enrollments.course_id==course_id).first()
    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )
    cache_key = f"announcements_course_{course_id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        print("Cache Hit!")
        return json.loads(cached_data)
    print("Cache Miss!")
    announcements = db.query(models.Announcement).filter(models.Announcement.course_id==course_id).all()
    announcement_list = [
        schemas.AnnouncementResponse.model_validate(announcement).model_dump()
        for announcement in announcements
    ]
    redis_client.setex(
        cache_key,
        300,
        json.dumps(announcement_list)
    )
    return announcement_list
    
@app.post("/Course",response_model=schemas.CourseResponse)
def post_course(
    course:schemas.CourseCreate,
    current_teacher:models.Teacher = Depends(oauth2.get_current_teacher),
    db:Session=Depends(get_db)
):
    new_course = models.Course(**course.model_dump(), teacher_id=current_teacher.id)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@app.post("/Enrollments")
def enrollment(
    course_id:int,
    db:Session=Depends(get_db),
    current_student:models.Student=Depends(oauth2.get_current_student)
):
    course = db.query(models.Course).filter(models.Course.id==course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course Not Found")
    
    existing_enrollment = db.query(models.Enrollments).filter(models.Enrollments.student_id==current_student.id,
                                                              models.Enrollments.course_id==course_id).first()
    
    if existing_enrollment:
        raise HTTPException(status_code=404, detail="Already Enrolled!")
    
    new_enrollment = models.Enrollments(
        student_id = current_student.id,
        course_id = course_id
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    send_registration_email.delay(current_student.email,course.name)
    redis_client.delete(f"courses_student_{current_student.id}")
    redis_client.delete(f"assignments_student{current_student.id}")
    return {"message":"Enrolled Successfully"}


@app.post("/Assignment",response_model=schemas.AssignmentResponse)
def post_assignment(
    assignment:schemas.AssignmentCreate,
    db:Session=Depends(get_db),
    current_teacher:models.Teacher=Depends(oauth2.get_current_teacher)
):
    course = db.query(models.Course).filter(models.Course.id==assignment.course_id,
                                            models.Course.teacher_id==current_teacher.id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="No Course Found")
    
    new_assignment = models.Assignment(
        **assignment.model_dump()
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    enrollments = db.query(models.Enrollments).filter(models.Enrollments.course_id == assignment.course_id)\
    .all()
    for e in enrollments:
        redis_client.delete(f"assignments_students_{e.student_id}")
    return new_assignment

@app.post("/Assignment/Upload")
async def upload_assignment(
    assignment_id:int,
    file : UploadFile = File(...),
    db:Session=Depends(get_db),
    current_student:models.Student=Depends(oauth2.get_current_student)
):
    assignment = db.query(models.Assignment)\
    .join(models.Course)\
    .join(models.Enrollments, models.Course.id == models.Enrollments.course_id)\
    .filter(models.Assignment.id == assignment_id, 
            models.Enrollments.student_id == current_student.id)\
    .first()
    
    if not assignment:
        raise HTTPException(status_code=404,detail="Assignment Not Found")
    
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    file_location = f"uploads/student_{current_student.id}_{file.filename}"

    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    return{"info": f"File '{file.filename}' uploaded successfully for Assignment: {assignment.title}"}

@app.post("/Announcements", response_model=schemas.AnnouncementResponse)
def post_announcement(
    announcement: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(oauth2.get_current_teacher)
):
    course = db.query(models.Course).filter(
        models.Course.id == announcement.course_id,
        models.Course.teacher_id == current_teacher.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to post in this course."
        )

    new_announcement = models.Announcement(
        **announcement.model_dump(exclude={"teacher_id"}), 
        teacher_id=current_teacher.id 
    )
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    redis_client.delete("announcements_course_{models.course.id}")
    return new_announcement


    






    

     

   



