from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Date
from datetime import date


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    courses = relationship("Course", secondary="enrollments", back_populates="students")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    title = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    students = relationship("Student", secondary="enrollments", back_populates="courses")
    teacher = relationship("Teacher", back_populates="courses")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete")
    announcements = relationship("Announcement", back_populates="course", cascade="all, delete")


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    courses = relationship("Course", back_populates="teacher")
    announcements = relationship("Announcement", back_populates="author")


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

    author = relationship("Teacher", back_populates="announcements")
    course = relationship("Course", back_populates="announcements")

class Enrollments(Base):
    __tablename__ = "enrollments"
    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
   
class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="assignments")