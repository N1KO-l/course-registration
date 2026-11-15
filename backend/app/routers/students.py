from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import hash_password, require_teacher
from ..database import get_db

router = APIRouter(prefix="/api/students", tags=["学生管理"], dependencies=[Depends(require_teacher)])


def _resolve_major_code(db: Session, major_name: str, major_code: str) -> str:
    """把专业名称/代码统一解析成 majors.code，保证两者一致。"""
    major_name = (major_name or "").strip()
    major_code = (major_code or "").strip()
    if major_name:
        major = db.query(models.Major).filter_by(name=major_name).first()
        if major is None:
            raise HTTPException(status_code=400, detail=f"未知专业：{major_name}")
        return major.code
    if major_code:
        major = db.query(models.Major).filter_by(code=major_code).first()
        if major is None:
            raise HTTPException(status_code=400, detail=f"未知专业代码：{major_code}")
        return major.code
    raise HTTPException(status_code=400, detail="专业不能为空")


@router.get("/", response_model=schemas.StudentPage)
def list_students(
    page: int = 1,
    page_size: int = 10,
    keyword: str = "",
    db: Session = Depends(get_db),
):
    query = db.query(models.Student)
    if keyword:
        like = f"%{keyword}%"
        query = query.outerjoin(models.Major, models.Student.major_code == models.Major.code)
        query = query.filter(or_(
            models.Student.name.like(like),
            models.Student.student_no.like(like),
            models.Major.name.like(like),
        ))
    total = query.count()
    page = max(page, 1)
    page_size = max(min(page_size, 10000), 1)
    items = query.order_by(models.Student.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


@router.post("/", response_model=schemas.StudentRead)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    data = student.model_dump()
    major_name = data.pop("major", "")
    data["major_code"] = _resolve_major_code(db, major_name, data.get("major_code"))
    db_student = models.Student(**data)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.get("/{student_id}", response_model=schemas.StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.put("/{student_id}", response_model=schemas.StudentRead)
def update_student(student_id: int, student: schemas.StudentCreate, db: Session = Depends(get_db)):
    db_student = db.get(models.Student, student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    data = student.model_dump()
    major_name = data.pop("major", "")
    major_code = data.pop("major_code", "")
    if major_name or major_code:
        data["major_code"] = _resolve_major_code(db, major_name, major_code)
    for key, value in data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.get(models.Student, student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    user = db.query(models.User).filter_by(student_id=student_id).first()
    if user is not None:
        db.delete(user)
    db.delete(db_student)
    db.commit()
    return {"ok": True}


@router.post("/batch-delete")
def batch_delete_students(req: schemas.BatchDeleteRequest, db: Session = Depends(get_db)):
    deleted = 0
    for sid in req.ids:
        student = db.get(models.Student, sid)
        if student is None:
            continue
        user = db.query(models.User).filter_by(student_id=sid).first()
        if user is not None:
            db.delete(user)
        db.delete(student)
        deleted += 1
    db.commit()
    return {"deleted_count": deleted}


@router.post("/{student_id}/reset-password")
def reset_password(student_id: int, req: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if not req.new_password:
        raise HTTPException(status_code=400, detail="新密码不能为空")

    user = db.query(models.User).filter_by(student_id=student_id).first()
    if user is None:
        user = models.User(
            username=student.student_no,
            hashed_password=hash_password(req.new_password),
            role="student",
            student_id=student_id,
        )
        db.add(user)
    else:
        user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"ok": True, "message": "密码已重置"}
