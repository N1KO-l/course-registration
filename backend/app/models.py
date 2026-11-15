from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import column_property, relationship

from .database import Base


class Major(Base):
    """专业字典表：name -> code，消除 students 表中的传递依赖。"""

    __tablename__ = "majors"

    code = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)

    students = relationship("Student", back_populates="major_rel")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    student_no = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    email = Column(String, default="")
    age = Column(Integer, default=0)
    grade = Column(String, default="")        # 年级，如 "2022"
    major_code = Column(String, ForeignKey("majors.code"), index=True)  # 三位专业代码，如 "013"
    gender = Column(String, default="")       # 性别，如 "男"/"女"
    id_card = Column(String, unique=True, nullable=True)  # 身份证号（18位，唯一）

    major_rel = relationship("Major", back_populates="students")

    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

    @property
    def major(self):
        """专业名称由 majors 表连接得到，不在 students 表中冗余存储。"""
        return self.major_rel.name if self.major_rel else ""


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    course_code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    credit = Column(Integer, default=3)
    capacity = Column(Integer, default=50)
    teacher = Column(String, default="")
    major = Column(String, default="", index=True)
    day = Column(String, default="")       # 星期几，如 "星期一"
    period = Column(String, default="")    # 时间段，如 "上午"/"下午"/"晚上"
    start_time = Column(String, default="")  # 开始时间，如 "14:00"
    end_time = Column(String, default="")    # 结束时间，如 "15:50"
    weeks = Column(String, default="")     # 周次，如 "第1-13周"

    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    enrolled_at = Column(DateTime, default=datetime.now)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="student")  # "teacher" 或 "student"
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)


# 已选人数由 SQL 聚合得到（相关子查询），避免 N+1 与 Python 端计数。
Course.enrolled_count = column_property(
    select(func.count(Enrollment.id))
    .where(Enrollment.course_id == Course.id)
    .correlate_except(Enrollment)
    .scalar_subquery()
)
