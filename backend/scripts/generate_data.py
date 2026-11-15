# -*- coding: utf-8 -*-
"""生成可复现的测试数据（学生、登录账号、选课记录）。

前提：已运行 seed.py（课程、专业字典、默认账号已就绪）。

用法（在 backend 目录下）：
    .venv/bin/python scripts/generate_data.py
    .venv/bin/python scripts/generate_data.py --students 5000 --enrollments 20000
    .venv/bin/python scripts/generate_data.py --students 500 --seed 7

说明：
  - 固定 --seed 时结果可复现；
  - 学生初始密码统一为 123456（共用同一个 PBKDF2 哈希以加快生成）；
  - 选课只在本专业课程或公共课/体育/英语中选择，且不超过课程容量。
"""
import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import models  # noqa: E402
from app.auth import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.majors import MAJOR_CODES  # noqa: E402
from app.routers.enrollments import (  # noqa: E402
    COMMON_MAJOR,
    FREE_ELECTIVE_MAJORS,
    MAX_COURSES,
    MAX_CREDITS,
    PE_MAJOR,
    _times_overlap,
)

SURNAMES = list("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤")
GIVEN = list("伟芳娜秀英敏静丽强磊军洋勇艳杰娟涛明超秀霞平刚桂英华玉兰萍红梅鑫宇轩浩然子涵雨欣佳怡思远晨曦嘉宁若溪")

FREE_MAJORS = {"公共课", "体育", "英语"}
DEFAULT_PASSWORD = "123456"


def build_student_no(rng: random.Random, grade: str, major_code: str, used: set[str]) -> str:
    for _ in range(500):
        no = f"{grade}{major_code}{rng.randint(0, 999):03d}"
        if no not in used:
            used.add(no)
            return no
    raise RuntimeError("学号空间不足，请减少生成数量或更换年级")


def build_id_card(seq: int, used: set[str]) -> str:
    # 6 位地区码 + 8 位出生日期 + 4 位顺序号 = 18 位；顺序号保证唯一
    birth = datetime(1998 + seq % 8, 1 + seq % 12, 1 + seq % 28)
    while True:
        card = f"110101{birth:%Y%m%d}{seq % 10000:04d}"
        seq += 1
        if card not in used:
            used.add(card)
            return card


def main() -> None:
    parser = argparse.ArgumentParser(description="生成可复现的学生/选课测试数据")
    parser.add_argument("--students", type=int, default=1000, help="生成学生数量")
    parser.add_argument("--enrollments", type=int, default=3000, help="生成选课记录数量")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--ignore-capacity", action="store_true",
                        help="生成选课时忽略课程容量限制（仅用于基准/压力测试）")
    parser.add_argument("--enroll-existing", action="store_true",
                        help="对数据库中已有学生生成选课记录（可用于填充演示数据）")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    db = SessionLocal()
    try:
        majors = db.query(models.Major).all()
        if not majors:
            raise SystemExit("majors 表为空，请先运行：.venv/bin/python seed.py")
        major_pairs = [(m.code, m.name) for m in majors]

        courses = db.query(models.Course).all()
        if not courses:
            raise SystemExit("courses 表为空，请先运行：.venv/bin/python seed.py")

        # 已有学号 / 身份证号，避免唯一约束冲突
        used_nos = {no for (no,) in db.query(models.Student.student_no).all() if no}
        used_cards = {card for (card,) in db.query(models.Student.id_card).all() if card}
        next_card_seq = len(used_cards) + 1

        shared_hash = hash_password(DEFAULT_PASSWORD)
        grades = ["2019", "2020", "2021", "2022", "2023", "2024"]

        created_students = []
        batch = []
        for i in range(args.students):
            code, major_name = rng.choice(major_pairs)
            grade = rng.choice(grades)
            no = build_student_no(rng, grade, code, used_nos)
            card = build_id_card(next_card_seq, used_cards)
            next_card_seq += 1
            name = rng.choice(SURNAMES) + "".join(rng.choice(GIVEN) for _ in range(rng.randint(1, 2)))
            student = models.Student(
                student_no=no,
                name=name,
                major_code=code,
                grade=grade,
                age=rng.randint(18, 28),
                gender=rng.choice(["男", "女"]),
                id_card=card,
                email=f"{no}@1.com",
            )
            batch.append(student)
            if len(batch) >= 500:
                db.add_all(batch)
                db.flush()
                created_students.extend(batch)
                batch = []
        if batch:
            db.add_all(batch)
            db.flush()
            created_students.extend(batch)

        db.add_all([
            models.User(
                username=s.student_no,
                hashed_password=shared_hash,
                role="student",
                student_id=s.id,
            )
            for s in created_students
        ])
        db.commit()
        print(f"已生成学生 {len(created_students)} 名，对应登录账号 {len(created_students)} 个（密码 {DEFAULT_PASSWORD}）")

        # 选课：只选本专业课程或公共课/体育/英语，并遵守容量
        major_name_by_code = {m.code: m.name for m in majors}
        student_pool = list(created_students)
        if args.enroll_existing:
            student_pool = db.query(models.Student).all()

        if args.enrollments > 0 and not student_pool:
            print("没有可用于选课的学生，跳过选课记录生成")
        elif args.enrollments > 0:
            courses_by_major: dict[str, list[models.Course]] = {}
            for c in courses:
                courses_by_major.setdefault(c.major, []).append(c)
            capacity_left = {c.id: max((c.capacity or 0) - c.enrolled_count, 0) for c in courses}

            # 每名学生当前已选课程与计数，生成时同步维护，保证不超过 5 门且不冲突
            course_by_id = {c.id: c for c in courses}
            states = {
                s.id: {"courses": [], "credits": 0, "public": 0, "pe": 0}
                for s in student_pool
            }
            for e in db.query(models.Enrollment).all():
                st = states.get(e.student_id)
                c = course_by_id.get(e.course_id)
                if st is None or c is None:
                    continue
                st["courses"].append(c)
                if c.major == COMMON_MAJOR:
                    st["public"] += 1
                if c.major == PE_MAJOR:
                    st["pe"] += 1
                if c.major not in FREE_ELECTIVE_MAJORS:
                    st["credits"] += c.credit

            pairs = set(db.query(models.Enrollment.student_id, models.Enrollment.course_id).all())
            enrolled = 0
            attempts = 0
            max_attempts = args.enrollments * 20
            now = datetime.now()
            while enrolled < args.enrollments and attempts < max_attempts:
                attempts += 1
                student = rng.choice(student_pool)
                major_name = major_name_by_code.get(student.major_code, "")
                eligible = courses_by_major.get(major_name, []) + [
                    c for m in FREE_MAJORS for c in courses_by_major.get(m, [])
                ]
                if not eligible:
                    continue
                course = rng.choice(eligible)
                if not args.ignore_capacity and capacity_left.get(course.id, 0) <= 0:
                    continue

                st = states[student.id]
                if len(st["courses"]) >= MAX_COURSES:
                    continue
                if course.major == COMMON_MAJOR and st["public"] >= 1:
                    continue
                if course.major == PE_MAJOR and st["pe"] >= 1:
                    continue
                if course.major not in FREE_ELECTIVE_MAJORS and st["credits"] + course.credit > MAX_CREDITS:
                    continue
                if any(_times_overlap(course, c) for c in st["courses"]):
                    continue

                key = (student.id, course.id)
                if key in pairs:
                    continue
                pairs.add(key)
                if not args.ignore_capacity:
                    capacity_left[course.id] -= 1
                enrolled_at = now - timedelta(
                    days=rng.randint(0, 30),
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                )
                db.add(models.Enrollment(
                    student_id=student.id,
                    course_id=course.id,
                    enrolled_at=enrolled_at,
                ))
                st["courses"].append(course)
                if course.major == COMMON_MAJOR:
                    st["public"] += 1
                if course.major == PE_MAJOR:
                    st["pe"] += 1
                if course.major not in FREE_ELECTIVE_MAJORS:
                    st["credits"] += course.credit
                enrolled += 1
                if enrolled % 1000 == 0:
                    db.commit()
            db.commit()
            print(f"已生成选课记录 {enrolled} 条（尝试 {attempts} 次）")

        for table, model in [("majors", models.Major), ("students", models.Student),
                             ("courses", models.Course), ("enrollments", models.Enrollment),
                             ("users", models.User)]:
            print(f"  {table}: {db.query(model).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
