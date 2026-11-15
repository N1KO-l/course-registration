from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user, require_teacher
from ..database import get_db

router = APIRouter(prefix="/api/courses", tags=["课程管理"])


def _validate_course_time(course: schemas.CourseCreate) -> None:
    """课程必须有完整的星期与起止时间，且单次课程固定 2 小时。"""
    if not course.day or not course.start_time or not course.end_time:
        raise HTTPException(status_code=400, detail="请完整填写上课星期、开始时间和结束时间")
    try:
        start_hour, start_minute = map(int, course.start_time.split(":"))
        end_hour, end_minute = map(int, course.end_time.split(":"))
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式应为 HH:MM")
    if end_hour * 60 + end_minute - (start_hour * 60 + start_minute) != 120:
        raise HTTPException(status_code=400, detail="单次课程时长必须为 2 小时")


@router.get("/", response_model=list[schemas.CourseRead])
def list_courses(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.Course).order_by(models.Course.id).all()


@router.post("/", response_model=schemas.CourseRead)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db), _user: models.User = Depends(require_teacher)):
    _validate_course_time(course)
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@router.get("/{course_id}", response_model=schemas.CourseRead)
def get_course(course_id: int, db: Session = Depends(get_db), _user: models.User = Depends(require_teacher)):
    course = db.get(models.Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.put("/{course_id}", response_model=schemas.CourseRead)
def update_course(course_id: int, course: schemas.CourseCreate, db: Session = Depends(get_db), _user: models.User = Depends(require_teacher)):
    db_course = db.get(models.Course, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _validate_course_time(course)
    for key, value in course.model_dump().items():
        setattr(db_course, key, value)
    db.commit()
    db.refresh(db_course)
    return db_course


@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), _user: models.User = Depends(require_teacher)):
    db_course = db.get(models.Course, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    db.delete(db_course)
    db.commit()
    return {"ok": True}
