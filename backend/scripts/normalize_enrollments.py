# -*- coding: utf-8 -*-
"""清理历史选课数据，使其满足当前选课规则：

  1. 每名学生最多 5 门课；
  2. 同一天的上课时间不能重叠（单次课程 2 小时）；
  3. 公共课最多 1 门、体育课最多 1 门；
  4. 计入总学分不超过 17（体育/英语不计入）。

按选课时间从早到晚保留，删除违反规则的后选记录。

用法（在 backend 目录下）：
    .venv/bin/python scripts/normalize_enrollments.py
    .venv/bin/python scripts/normalize_enrollments.py --dry-run
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import models  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.routers.enrollments import (  # noqa: E402
    COMMON_MAJOR,
    FREE_ELECTIVE_MAJORS,
    MAX_COURSES,
    MAX_CREDITS,
    PE_MAJOR,
    _times_overlap,
)


def normalize(dry_run: bool = False) -> None:
    db = SessionLocal()
    try:
        students = db.query(models.Student).all()
        removed = 0
        checked = 0
        for student in students:
            if not student.enrollments:
                continue
            checked += 1
            ordered = sorted(
                student.enrollments,
                key=lambda e: (e.enrolled_at or datetime.min, e.id),
            )
            kept: list[models.Course] = []
            counted_credits = 0
            public_count = 0
            pe_count = 0
            for enrollment in ordered:
                course = enrollment.course
                allowed = (
                    course.major == student.major
                    or course.major == COMMON_MAJOR
                    or course.major in FREE_ELECTIVE_MAJORS
                )
                if allowed and len(kept) < MAX_COURSES:
                    allowed = not any(_times_overlap(course, c) for c in kept)
                else:
                    allowed = False
                if allowed and course.major == COMMON_MAJOR and public_count >= 1:
                    allowed = False
                if allowed and course.major == PE_MAJOR and pe_count >= 1:
                    allowed = False
                if allowed and course.major not in FREE_ELECTIVE_MAJORS:
                    allowed = counted_credits + course.credit <= MAX_CREDITS

                if allowed:
                    kept.append(course)
                    if course.major == COMMON_MAJOR:
                        public_count += 1
                    if course.major == PE_MAJOR:
                        pe_count += 1
                    if course.major not in FREE_ELECTIVE_MAJORS:
                        counted_credits += course.credit
                else:
                    removed += 1
                    if not dry_run:
                        db.delete(enrollment)
            if not dry_run and checked % 200 == 0:
                db.commit()
        if dry_run:
            db.rollback()
        else:
            db.commit()
        print(f"检查学生 {checked} 名，{'将删除' if dry_run else '已删除'}选课记录 {removed} 条")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="清理不满足选课规则的历史记录")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不实际删除")
    args = parser.parse_args()
    normalize(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
