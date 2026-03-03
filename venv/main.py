from fastapi import FastAPI, Depends, HTTPException,status, Response,Query, File, UploadFile
from sqlalchemy.orm import Session
from database import Engine, get_db
import schemas, models, oauth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os

models.Base.metadata.create_all(bind=Engine)

app = FastAPI()

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
    student = db.query(models.Student).filter(models.Student.email == credentials.username).first()
    if student and oauth2.verify_password(credentials.password, student.password):
        token = oauth2.create_access_token(data={"student_id": student.id})
        return {"access_token": token, "token_type": "bearer"}
    
    teacher = db.query(models.Teacher).filter(models.Teacher.email == credentials.username).first()
    if teacher and oauth2.verify_password(credentials.password, teacher.password):
        token = oauth2.create_access_token(data={"teacher_id": teacher.id})
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Invalid Credentials")


@app.get("/Courses",response_model=list[schemas.CourseResponse])
def registered_Courses(
    db:Session=Depends(get_db),
    current_student:models.Student=Depends(oauth2.get_current_student)
):
    return current_student.courses
    
@app.get("/Assignments",response_model=list[schemas.AssignmentResponse])
def get_assignments(
    db:Session=Depends(get_db),
    current_student:models.Student=Depends(oauth2.get_current_student)    
):
    assignment = db.query(models.Assignment)\
    .join(models.Course)\
    .join(models.Enrollments)\
    .filter(models.Enrollments.student_id==current_student.id)\
    .all()
    return assignment

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

    announcement = db.query(models.Announcement).filter(models.Announcement.course_id==course_id).all()
    return announcement
    
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
    # 1. THE QUERY: This looks for a match where the course belongs to the logged-in teacher
    course = db.query(models.Course).filter(
        models.Course.id == announcement.course_id,
        models.Course.teacher_id == current_teacher.id
    ).first()

    # 2. THE SECURITY CHECK: If no match is found, 'course' is None
    if not course:
        # This stops the process and prevents the announcement from being created
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to post in this course."
        )

    # 3. THE CREATION: Only happens if the check above passes
    new_announcement = models.Announcement(
        **announcement.model_dump(exclude={"teacher_id"}), 
        teacher_id=current_teacher.id # Force the ID from the secure token
    )
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    return new_announcement