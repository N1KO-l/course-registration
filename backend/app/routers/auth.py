import io
import random

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openpyxl import load_workbook
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import create_access_token, get_current_user, hash_password, require_teacher, verify_password
from ..database import get_db
from ..majors import MAJOR_CODES

router = APIRouter(prefix="/api/auth", tags=["认证"])

DEFAULT_PASSWORD = "123456"  # 学生初始密码


@router.post("/login", response_model=schemas.Token)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    account = req.account.strip()
    user = db.query(models.User).filter_by(username=account).first()
    if user is None:
        # 尝试按邮箱查学生
        student = db.query(models.Student).filter_by(email=account).first()
        if student is not None:
            user = db.query(models.User).filter_by(student_id=student.id).first()
    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="账号或密码错误")

    token = create_access_token(user.username, user.role)
    major, name = None, None
    if user.role == "student" and user.student_id is not None:
        student = db.get(models.Student, user.student_id)
        if student is not None:
            major, name = student.major, student.name

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "student_id": user.student_id,
        "major": major,
        "name": name,
    }


def _generate_student_no(grade: str, major_code: str, db: Session) -> str:
    """学号 = 年级 + 专业代码 + 随机三位数，随机部分自动查重。"""
    prefix = grade + major_code
    for _ in range(100):
        suffix = f"{random.randint(0, 999):03d}"
        no = prefix + suffix
        if not db.query(models.Student).filter_by(student_no=no).first():
            return no
    raise HTTPException(status_code=400, detail="学号生成失败，请重试")


def _is_valid_id_card(id_card: str) -> bool:
    """校验 18 位身份证号格式：前 17 位数字，末位数字或 X。"""
    if len(id_card) != 18:
        return False
    if not id_card[:17].isdigit():
        return False
    return id_card[17].isdigit() or id_card[17].upper() == "X"


def _register_students(items: list[dict], db: Session) -> dict:
    """批量注册学生（items 每项含 name/grade/major/age/gender/id_card），自动生成学号、邮箱、初始密码。"""
    created, skipped = [], []
    for item in items:
        name = str(item.get("name", "")).strip()
        grade = str(item.get("grade", "")).strip()
        major = str(item.get("major", "")).strip()
        if not name or not grade or not major:
            skipped.append({"name": name, "reason": "姓名/年级/专业不能为空"})
            continue
        major_code = MAJOR_CODES.get(major)
        if major_code is None:
            skipped.append({"name": name, "reason": f"未找到专业「{major}」的专业代码"})
            continue

        id_card = str(item.get("id_card", "")).strip().upper()
        if not _is_valid_id_card(id_card):
            skipped.append({"name": name, "reason": "身份证号格式错误（需 18 位）"})
            continue
        if db.query(models.Student).filter_by(id_card=id_card).first():
            skipped.append({"name": name, "reason": "身份证号已存在"})
            continue

        if db.query(models.Major).filter_by(code=major_code).first() is None:
            db.add(models.Major(code=major_code, name=major))

        student_no = _generate_student_no(grade, major_code, db)
        email = f"{student_no}@1.com"
        student = models.Student(
            student_no=student_no,
            name=name,
            grade=grade,
            major_code=major_code,
            age=item.get("age", 0),
            gender=item.get("gender", ""),
            id_card=id_card,
            email=email,
        )
        db.add(student)
        db.flush()  # 拿到 student.id
        db.add(models.User(
            username=student_no,
            hashed_password=hash_password(DEFAULT_PASSWORD),
            role="student",
            student_id=student.id,
        ))
        created.append({"student_no": student_no, "name": name, "email": email})

    db.commit()
    return {"created_count": len(created), "created": created, "skipped": skipped}


@router.post("/batch-register")
def batch_register(
    req: schemas.BatchRegisterRequest,
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_teacher),
):
    items = [item.model_dump() for item in req.students]
    return _register_students(items, db)


def _cell_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _cell_int(v) -> int:
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


@router.post("/import-excel")
async def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: models.User = Depends(require_teacher),
):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="请上传 .xlsx 或 .xls 文件")

    content = await file.read()
    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=400, detail="无法解析该 Excel 文件")

    ws = wb.active
    items = []
    # 列顺序：姓名、年级、专业、年龄、性别（第一行为表头，跳过）
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row is None or not any(row):
            continue
        items.append({
            "name": _cell_str(row[0]) if len(row) > 0 else "",
            "grade": _cell_str(row[1]) if len(row) > 1 else "",
            "major": _cell_str(row[2]) if len(row) > 2 else "",
            "age": _cell_int(row[3]) if len(row) > 3 else 0,
            "gender": _cell_str(row[4]) if len(row) > 4 else "",
            "id_card": _cell_str(row[5]) if len(row) > 5 else "",
        })

    if not items:
        raise HTTPException(status_code=400, detail="Excel 中没有数据")

    return _register_students(items, db)


@router.get("/me", response_model=schemas.UserRead)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    req: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not verify_password(req.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    if not req.new_password:
        raise HTTPException(status_code=400, detail="新密码不能为空")
    user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"ok": True, "message": "密码修改成功"}
