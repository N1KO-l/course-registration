from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/students", tags=["选课管理"])

COMMON_MAJOR = "公共课"           # 思政类公共课，最多选 1 门，计入总学分
PE_MAJOR = "体育"                 # 体育课，最多选 1 门，不计入学分
FREE_ELECTIVE_MAJORS = {"体育", "英语"}  # 不计入学分的课程类别
MAX_CREDITS = 17                  # 总学分上限
MAX_COURSES = 5                   # 每名学生最多选 5 门课


def _to_minutes(value: str) -> int | None:
    """把 HH:MM 转成分钟数，格式不合法时返回 None。"""
    try:
        hour, minute = value.split(":")
        return int(hour) * 60 + int(minute)
    except (AttributeError, ValueError):
        return None


def _times_overlap(course_a: models.Course, course_b: models.Course) -> bool:
    """两门课是否在同一天且时间区间重叠（单次课程均为 2 小时）。"""
    if not course_a.day or not course_b.day or course_a.day != course_b.day:
        return False
    a_start, a_end = _to_minutes(course_a.start_time), _to_minutes(course_a.end_time)
    b_start, b_end = _to_minutes(course_b.start_time), _to_minutes(course_b.end_time)
    if None in (a_start, a_end, b_start, b_end):
        return False
    return a_start < b_end and b_start < a_end


def _check_access(user: models.User, student_id: int):
    if user.role != "teacher" and user.student_id != student_id:
        raise HTTPException(status_code=403, detail="只能操作自己的选课")


@router.get("/{student_id}/courses", response_model=list[schemas.CourseRead])
def list_enrolled_courses(
    student_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _check_access(user, student_id)
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return [e.course for e in student.enrollments]


@router.post("/{student_id}/courses")
def enroll(
    student_id: int,
    req: schemas.EnrollRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _check_access(user, student_id)
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    course = db.get(models.Course, req.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")

    if db.query(models.Enrollment).filter_by(student_id=student_id, course_id=course.id).first():
        raise HTTPException(status_code=400, detail="该学生已选此课程")

    if course.enrolled_count >= course.capacity:
        raise HTTPException(status_code=400, detail="课程已满，无法选课")

    # 只能选本专业课程（公共课、体育、英语对所有学生开放）
    if course.major != student.major and course.major != COMMON_MAJOR and course.major not in FREE_ELECTIVE_MAJORS:
        raise HTTPException(status_code=400, detail=f"只能选择本专业（{student.major}）的课程")

    enrollments = db.query(models.Enrollment).filter_by(student_id=student_id).all()

    # 每名学生最多选 5 门课
    if len(enrollments) >= MAX_COURSES:
        raise HTTPException(status_code=400, detail=f"最多只能选 {MAX_COURSES} 门课程")

    # 已选课程的上课时间不能与新课程冲突（同一天且时间区间重叠）
    for enrollment in enrollments:
        if _times_overlap(course, enrollment.course):
            raise HTTPException(
                status_code=400,
                detail=f"时间冲突：与已选课程「{enrollment.course.name}」的上课时间重叠",
            )

    # 公共课最多选一门
    if course.major == COMMON_MAJOR:
        if any(e.course.major == COMMON_MAJOR for e in enrollments):
            raise HTTPException(status_code=400, detail="公共课最多只能选一门")

    # 体育课最多选一门
    if course.major == PE_MAJOR:
        if any(e.course.major == PE_MAJOR for e in enrollments):
            raise HTTPException(status_code=400, detail="体育课最多只能选一门")

    # 总学分不超过 17（体育、英语不计入学分）
    if course.major not in FREE_ELECTIVE_MAJORS:
        counted = sum(e.course.credit for e in enrollments if e.course.major not in FREE_ELECTIVE_MAJORS)
        if counted + course.credit > MAX_CREDITS:
            raise HTTPException(status_code=400, detail=f"总学分不能超过 {MAX_CREDITS} 学分")

    db.add(models.Enrollment(student_id=student_id, course_id=course.id))
    db.commit()
    return {"ok": True, "message": "选课成功"}


@router.delete("/{student_id}/courses/{course_id}")
def drop(
    student_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _check_access(user, student_id)
    enrollment = db.query(models.Enrollment).filter_by(student_id=student_id, course_id=course_id).first()
    if enrollment is None:
        raise HTTPException(status_code=404, detail="未选此课程")
    db.delete(enrollment)
    db.commit()
    return {"ok": True, "message": "退课成功"}
