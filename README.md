University Portal API 🎓
A robust, secure backend system built with FastAPI and SQLAlchemy. This portal manages the core interactions between university faculty and students, including course registration, assignment distribution, and secure file submissions.

Key Features
Dual-Role Authentication: Secure login system that distinguishes between Students and Teachers using distinct JWT payload keys.

Relational Course Management: Teachers can create courses and assignments, automatically linked to their unique Teacher ID.

Many-to-Many Enrollments: Students can enroll in multiple courses, handled via an efficient association table.

Strict Access Control: Students can only view or upload assignments for courses they are officially enrolled in.

Secure File Handling: Asynchronous assignment uploads with unique naming conventions to prevent data overwriting.

Tech Stack
Backend Framework: FastAPI (Asynchronous Python)

ORM: SQLAlchemy

Database: SQLite (managed via database.py)

Security: JWT (JSON Web Tokens) & Passlib (PBKDF2 Password Hashing)

Validation: Pydantic Schemas

Project Structure
I├── main.py          # API entry point and route definitions
├── models.py        # SQLAlchemy database tables (Student, Teacher, Course, Announcement, etc.)
├── schemas.py       # Pydantic data validation schemas
├── database.py      # Database engine and session configuration
├── oauth2.py        # JWT Token and Authentication logic
└── uploads/         # Directory for student assignment files

View Interactive Docs:
Visit http://127.0.0.1:8000/docs to test the API directly through the Swagger UI.

Core API Workflow
1. User Identity & Authentication
The system uses a unified authentication gateway to manage different roles within the university.

Dual-Role Registration: Separate endpoints allow for the creation of Student (/register) and Teacher (/Register/Teacher) accounts.

Unified Secure Login: A single /login endpoint that identifies whether the user is a student or teacher, verifying hashed passwords and issuing a role-specific JWT Bearer token.

Role-Based Access Control (RBAC): Most endpoints are "locked" (secured with a padlock icon in the documentation), requiring a valid token to verify permissions before granting access to data.
2. Teacher Privileges
Teachers act as the administrators for their specific academic content.

Course Creation: Teachers can launch new subjects via the POST /Course endpoint.

Courses are defined by a title (e.g., "Intro to Physics") and a name (e.g., "PHYS101").

Announcements: Teachers can post updates to their specific courses using POST /Announcements.

The system validates that the teacher owns the course before allowing the post.

Assignment Management: Teachers can create specific tasks for their courses using POST /Assignment, which are then made available to all enrolled students.
3. Student Privileges
Students interact with the academic content curated by teachers.

Course Enrollment: Students join specific subjects using the POST /Enrollments endpoint by providing a unique course_id.

Academic Dashboard:

View Registered Courses: Students can retrieve a personalized list of all courses they are currently enrolled in via GET /Courses.

View Assignments: Access a list of all active assignments across their enrolled courses via GET /Assignments.

Secure Submissions: Students can upload their completed work through POST /Assignment/Upload.

The system validates that the student is actually enrolled in the course before accepting the file.
4. System & Data Integrity
Automated Storage: Uploaded files are safely stored in a dedicated uploads/ directory on the server, organized with unique naming conventions to prevent data loss.

Relational Database Mapping: The portal uses a relational structure where assignments are linked to courses, and courses are linked to both a teacher and multiple students (Many-to-Many).

Input Validation: All data entering the system (like the Course schema with title and name) is validated against Pydantic models to ensure data quality.

Security Implementation
Password Hashing: No plain-text passwords are stored; all are salted and hashed using PBKDF2.

Scoped Dependencies: Routes are protected by get_current_student or get_current_teacher to prevent role-crossing.

CORS & Error Handling: Implements standard HTTP status codes (401 for unauthorized, 404 for missing resources).