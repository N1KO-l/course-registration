-- ============================================================
-- Student Course Registration System -- canonical SQLite schema
-- 与 app/models.py 中的 SQLAlchemy 模型保持一致（3NF）。
--
-- 关系：
--   majors 1 -- N students
--   students 1 -- N enrollments N -- 1 courses
--   students 1 -- 1 users（仅学生角色）
--
-- 在 sqlite3 中执行：
--   sqlite3 students.db < schema.sql
-- 注意：PRAGMA foreign_keys 是"每连接"设置，应用连接时也必须开启
--       （见 app/database.py 的 connect 事件）。
-- ============================================================

PRAGMA foreign_keys = ON;

-- 专业字典表：消除 students 中 major -> major_code 的传递依赖
CREATE TABLE majors (
    code VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (code)
);
CREATE UNIQUE INDEX ix_majors_name ON majors (name);

CREATE TABLE students (
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
);
CREATE UNIQUE INDEX ix_students_student_no ON students (student_no);
CREATE INDEX ix_students_name ON students (name);
CREATE INDEX ix_students_major_code ON students (major_code);

CREATE TABLE courses (
    id INTEGER NOT NULL,
    course_code VARCHAR,
    name VARCHAR,
    credit INTEGER,
    capacity INTEGER,
    teacher VARCHAR,
    major VARCHAR,
    day VARCHAR,
    period VARCHAR,
    start_time VARCHAR,
    end_time VARCHAR,
    weeks VARCHAR,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_courses_course_code ON courses (course_code);
CREATE INDEX ix_courses_name ON courses (name);
CREATE INDEX ix_courses_major ON courses (major);

CREATE TABLE enrollments (
    id INTEGER NOT NULL,
    student_id INTEGER,
    course_id INTEGER,
    enrolled_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT uq_student_course UNIQUE (student_id, course_id),
    FOREIGN KEY(student_id) REFERENCES students (id),
    FOREIGN KEY(course_id) REFERENCES courses (id)
);
CREATE INDEX ix_enrollments_course_id ON enrollments (course_id);

CREATE TABLE users (
    id INTEGER NOT NULL,
    username VARCHAR,
    hashed_password VARCHAR,
    role VARCHAR,
    student_id INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY(student_id) REFERENCES students (id)
);
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE INDEX ix_users_student_id ON users (student_id);
