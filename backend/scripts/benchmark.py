# -*- coding: utf-8 -*-
"""对关键查询做简单基准测试，并打印 SQLite 查询计划。

用法（在 backend 目录下）：
    .venv/bin/python scripts/benchmark.py
    .venv/bin/python scripts/benchmark.py --repeat 50

输出可直接用于项目报告的 "Evaluation and Results" 一节。
"""
import argparse
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, or_, text  # noqa: E402

from app import models  # noqa: E402
from app.database import SessionLocal  # noqa: E402


def timed(fn, repeat: int):
    for _ in range(2):  # 预热
        fn()
    start = time.perf_counter()
    for _ in range(repeat):
        fn()
    return (time.perf_counter() - start) / repeat * 1000


def main() -> None:
    parser = argparse.ArgumentParser(description="关键查询基准测试")
    parser.add_argument("--repeat", type=int, default=20, help="每个查询重复次数")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        counts = {
            "students": db.query(models.Student).count(),
            "courses": db.query(models.Course).count(),
            "enrollments": db.query(models.Enrollment).count(),
            "users": db.query(models.User).count(),
        }
        print("数据量:", ", ".join(f"{k}={v}" for k, v in counts.items()))
        print()

        page_size = 20
        last_page = max(counts["students"] // page_size, 1)

        def page_one():
            db.query(models.Student).order_by(models.Student.id).offset(0).limit(page_size).all()

        def page_last():
            db.query(models.Student).order_by(models.Student.id).offset((last_page - 1) * page_size).limit(page_size).all()

        like = "%王%"

        def keyword_search():
            q = db.query(models.Student).outerjoin(
                models.Major, models.Student.major_code == models.Major.code
            )
            q.filter(or_(
                models.Student.name.like(like),
                models.Student.student_no.like(like),
                models.Major.name.like(like),
            )).all()

        def course_counts_group_by():
            (db.query(models.Course.id, models.Course.name, func.count(models.Enrollment.id))
               .outerjoin(models.Enrollment, models.Enrollment.course_id == models.Course.id)
               .group_by(models.Course.id, models.Course.name)
               .order_by(func.count(models.Enrollment.id).desc())
               .limit(10).all())

        def courses_with_enrolled_count():
            db.query(models.Course).all()

        def enrollments_by_course():
            db.query(models.Enrollment).filter(models.Enrollment.course_id == 1).all()

        benchmarks = [
            ("分页：第 1 页 (LIMIT 20)", page_one),
            (f"分页：最后一页 (OFFSET {(last_page - 1) * page_size})", page_last),
            ("关键字搜索 (LIKE '%王%'，含专业名)", keyword_search),
            ("每门课已选人数 (COUNT + GROUP BY)", course_counts_group_by),
            ("课程列表 + enrolled_count (相关子查询)", courses_with_enrolled_count),
            ("按课程查选课记录 (course_id 索引)", enrollments_by_course),
        ]

        print(f"{'查询':<48}{'平均耗时 (ms)':>14}")
        print("-" * 64)
        for label, fn in benchmarks:
            ms = timed(fn, args.repeat)
            print(f"{label:<48}{ms:>14.2f}")

        print("\n查询计划 (EXPLAIN QUERY PLAN):")
        plans = [
            ("分页", f"SELECT id FROM students ORDER BY id LIMIT {page_size} OFFSET {(last_page - 1) * page_size}"),
            ("按课程统计", "SELECT course_id, COUNT(*) FROM enrollments WHERE course_id = 1 GROUP BY course_id"),
            ("按课程名筛选", "SELECT id FROM courses WHERE major = '数据科学'"),
            ("学生按专业连接", "SELECT s.id FROM students s JOIN majors m ON s.major_code = m.code WHERE m.name = '数据科学'"),
        ]
        for label, sql in plans:
            print(f"\n-- {label}")
            print(f"   {sql}")
            for row in db.execute(text("EXPLAIN QUERY PLAN " + sql)):
                print("   ", tuple(row))
    finally:
        db.close()


if __name__ == "__main__":
    main()
