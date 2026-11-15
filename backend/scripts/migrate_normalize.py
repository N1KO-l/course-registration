# -*- coding: utf-8 -*-
"""把旧的 students.db 迁移到规范化 schema（3NF）。

改动内容：
  1. 新增 majors(code, name) 专业字典表；
  2. students 表删除冗余的 major 列，只保留 major_code 外键；
  3. 为外键/筛选列补充索引；
  4. 迁移过程自动备份原数据库（除非指定 --no-backup）。

用法（在 backend 目录下）：
    .venv/bin/python scripts/migrate_normalize.py
    .venv/bin/python scripts/migrate_normalize.py --db path/to/students.db
"""
import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 允许从 backend/ 直接运行
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.majors import MAJOR_CODES  # noqa: E402

DEFAULT_DB = BACKEND_DIR / "students.db"

CREATE_MAJORS = """
CREATE TABLE IF NOT EXISTS majors (
    code VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (code)
)
"""

CREATE_STUDENTS_NEW = """
CREATE TABLE students_new (
    id INTEGER NOT NULL,
    student_no VARCHAR,
    name VARCHAR,
    email VARCHAR,
    age INTEGER,
    grade VARCHAR,
    major_code VARCHAR,
    gender VARCHAR,
    id_card VARCHAR,
    PRIMARY KEY (id),
    FOREIGN KEY(major_code) REFERENCES majors (code),
    UNIQUE (id_card)
)
"""

INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_majors_name ON majors (name)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_students_student_no ON students (student_no)",
    "CREATE INDEX IF NOT EXISTS ix_students_name ON students (name)",
    "CREATE INDEX IF NOT EXISTS ix_students_major_code ON students (major_code)",
    "CREATE INDEX IF NOT EXISTS ix_courses_major ON courses (major)",
    "CREATE INDEX IF NOT EXISTS ix_enrollments_course_id ON enrollments (course_id)",
    "CREATE INDEX IF NOT EXISTS ix_users_student_id ON users (student_id)",
]


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def migrate(db_path: Path, backup: bool = True) -> None:
    if not db_path.exists():
        raise SystemExit(f"数据库不存在：{db_path}")

    if backup:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = db_path.with_name(f"{db_path.name}.bak-{stamp}")
        shutil.copy2(db_path, backup_path)
        print(f"已备份原数据库到：{backup_path}")

    conn = sqlite3.connect(db_path)
    conn.isolation_level = None  # 手动控制事务
    try:
        conn.execute("PRAGMA foreign_keys=OFF")

        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "students" not in tables:
            raise SystemExit("找不到 students 表，请先运行 seed.py 建表")

        conn.execute("BEGIN IMMEDIATE")

        # 1) 专业字典表
        conn.execute(CREATE_MAJORS)
        conn.executemany(
            "INSERT OR IGNORE INTO majors(code, name) VALUES (?, ?)",
            [(code, name) for name, code in MAJOR_CODES.items()],
        )

        has_legacy_major = "major" in table_columns(conn, "students")

        # 兼容旧数据里出现的其它专业名称
        if has_legacy_major:
            for major_name, major_code in conn.execute(
                "SELECT DISTINCT major, major_code FROM students WHERE major IS NOT NULL AND major <> ''"
            ).fetchall():
                code = major_code or MAJOR_CODES.get(major_name)
                if code:
                    conn.execute(
                        "INSERT OR IGNORE INTO majors(code, name) VALUES (?, ?)",
                        (code, major_name),
                    )

        # 2) 重建 students：去掉 major 列，改为 major_code 外键
        if has_legacy_major:
            conn.execute(CREATE_STUDENTS_NEW)
            conn.execute("""
                INSERT INTO students_new
                    (id, student_no, name, email, age, grade, major_code, gender, id_card)
                SELECT
                    id, student_no, name, email, age, grade,
                    COALESCE(
                        NULLIF(major_code, ''),
                        (SELECT code FROM majors WHERE majors.name = students.major)
                    ),
                    gender, id_card
                FROM students
            """)
            conn.execute("DROP TABLE students")
            conn.execute("ALTER TABLE students_new RENAME TO students")
            print("students 表已重建：删除 major 列，major_code 外键指向 majors.code")
        else:
            print("students 表已是规范化结构，跳过重建")

        # 3) 索引：先删除与主键/唯一约束重复的旧索引，再创建新索引
        for name in ("ix_students_id", "ix_courses_id", "ix_enrollments_id",
                     "ix_users_id", "ix_enrollments_student_id"):
            conn.execute(f"DROP INDEX IF EXISTS {name}")
        for sql in INDEXES:
            conn.execute(sql)

        conn.execute("COMMIT")
        conn.execute("PRAGMA foreign_keys=ON")

        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"foreign_key_check: {'OK' if not fk_errors else fk_errors}")
        print(f"integrity_check: {integrity}")

        for table in ("majors", "students", "courses", "enrollments", "users"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count}")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="规范化 students.db（新增 majors 表）")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="数据库文件路径")
    parser.add_argument("--no-backup", action="store_true", help="不备份原数据库")
    args = parser.parse_args()
    migrate(args.db, backup=not args.no_backup)


if __name__ == "__main__":
    main()
