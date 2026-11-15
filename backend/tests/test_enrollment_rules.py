# -*- coding: utf-8 -*-
"""选课规则、外键约束与聚合查询的单元测试。

运行（在 backend 目录下）：
    .venv/bin/python -m unittest discover -s tests -v
"""
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app import models, schemas
from app.database import Base
from app.routers.courses import create_course
from app.routers.enrollments import drop, enroll
from app.routers.students import create_student, list_students, update_student


class EnrollmentRulesTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test.db"
        self.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.db.add_all([
            models.Major(code="013", name="数据科学"),
            models.Major(code="014", name="计算机科学"),
        ])
        self.db.flush()

        self.s1 = models.Student(student_no="2022013001", name="张三", major_code="013",
                                 email="2022013001@1.com", age=22, grade="2022",
                                 gender="男", id_card="110101200001010011")
        self.s2 = models.Student(student_no="2022013002", name="李四", major_code="013",
                                 email="2022013002@1.com", age=21, grade="2022",
                                 gender="女", id_card="110101200001010022")
        self.db.add_all([self.s1, self.s2])
        self.db.flush()

        self.u1 = models.User(username=self.s1.student_no, hashed_password="x", role="student", student_id=self.s1.id)
        self.u2 = models.User(username=self.s2.student_no, hashed_password="x", role="student", student_id=self.s2.id)
        self.db.add_all([self.u1, self.u2])

        def course(code, major, credit=3, capacity=10, day="", start="", end=""):
            return models.Course(course_code=code, name=f"课程{code}", credit=credit,
                                 capacity=capacity, major=major,
                                 day=day, period="", start_time=start, end_time=end,
                                 weeks="第1-13周")

        # 每门课 2 小时；c1..c5 时间互不重叠，便于测试 5 门上限
        self.c1 = course("C001", "数据科学", day="星期一", start="08:30", end="10:30")
        self.c2 = course("C002", "数据科学", day="星期一", start="10:30", end="12:30")
        self.c3 = course("C003", "数据科学", day="星期二", start="08:30", end="10:30")
        self.c4 = course("C004", "数据科学", day="星期二", start="14:00", end="16:00")
        self.c5 = course("C005", "数据科学", day="星期三", start="08:30", end="10:30")
        self.c6 = course("C006", "数据科学", day="星期三", start="14:00", end="16:00")
        self.c7 = course("C007", "数据科学", day="星期四", start="08:30", end="10:30")
        self.c_other = course("C100", "计算机科学", day="星期四", start="14:00", end="16:00")
        self.c_cap = course("C200", "数据科学", capacity=1, day="星期五", start="08:30", end="10:30")
        self.c_pub1 = course("C300", "公共课", credit=2, day="星期五", start="14:00", end="16:00")
        self.c_pub2 = course("C301", "公共课", credit=2, day="星期五", start="19:00", end="21:00")
        self.c_pe1 = course("C400", "体育", credit=1, day="星期一", start="14:00", end="16:00")
        self.c_pe2 = course("C401", "体育", credit=1, day="星期一", start="19:00", end="21:00")
        self.c_eng = course("C500", "英语", credit=3, day="星期二", start="19:00", end="21:00")

        # 5 学分课程：4 门即 20 学分，用于测试 17 学分上限
        self.c_big1 = course("B001", "数据科学", credit=5, day="星期三", start="19:00", end="21:00")
        self.c_big2 = course("B002", "数据科学", credit=5, day="星期四", start="19:00", end="21:00")
        self.c_big3 = course("B003", "数据科学", credit=5, day="星期五", start="10:40", end="12:40")
        self.c_big4 = course("B004", "数据科学", credit=5, day="星期五", start="16:10", end="18:10")

        # 与 c1（星期一 08:30-10:30）时间重叠
        self.c_conflict = course("C900", "数据科学", day="星期一", start="09:00", end="11:00")

        self.db.add_all([
            self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7,
            self.c_other, self.c_cap, self.c_pub1, self.c_pub2,
            self.c_pe1, self.c_pe2, self.c_eng,
            self.c_big1, self.c_big2, self.c_big3, self.c_big4, self.c_conflict,
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.tmpdir.cleanup()

    # ---------- helpers ----------
    def _enroll(self, course, student=None, user=None):
        student = student or self.s1
        user = user or self.u1
        return enroll(student.id, schemas.EnrollRequest(course_id=course.id), self.db, user)

    def _assert_rejected(self, course, detail_part, student=None, user=None):
        with self.assertRaises(HTTPException) as ctx:
            self._enroll(course, student=student, user=user)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn(detail_part, ctx.exception.detail)

    # ---------- tests ----------
    def test_successful_enrollment(self):
        self.assertEqual(self._enroll(self.c1)["message"], "选课成功")
        self.assertEqual(self.db.query(models.Enrollment).count(), 1)

    def test_duplicate_enrollment_rejected(self):
        self._enroll(self.c1)
        self._assert_rejected(self.c1, "已选此课程")

    def test_capacity_rejected(self):
        # s2 先占满容量为 1 的课程，s1 再选应失败
        self._enroll(self.c_cap, student=self.s2, user=self.u2)
        self._assert_rejected(self.c_cap, "课程已满")

    def test_major_restriction(self):
        self._assert_rejected(self.c_other, "只能选择本专业")

    def test_public_course_limit(self):
        self._enroll(self.c_pub1)
        self._assert_rejected(self.c_pub2, "公共课最多只能选一门")

    def test_pe_course_limit(self):
        self._enroll(self.c_pe1)
        self._assert_rejected(self.c_pe2, "体育课最多只能选一门")

    def test_credit_limit(self):
        for c in (self.c_big1, self.c_big2, self.c_big3):
            self._enroll(c)  # 3 * 5 = 15 学分
        self._assert_rejected(self.c_big4, "总学分不能超过 17 学分")

    def test_free_elective_not_counted_in_credits(self):
        for c in (self.c_big1, self.c_big2, self.c_big3):
            self._enroll(c)  # 15 学分
        self._enroll(self.c_eng)  # 英语不计入；若计入则 18 学分会超限
        self.assertEqual(self.db.query(models.Enrollment).count(), 4)

    def test_max_five_courses(self):
        for c in (self.c1, self.c2, self.c3, self.c4, self.c5):
            self._enroll(c)
        self._assert_rejected(self.c6, "最多只能选 5 门课程")

    def test_time_conflict_rejected(self):
        self._enroll(self.c1)  # 星期一 08:30-10:30
        self._assert_rejected(self.c_conflict, "时间冲突")  # 星期一 09:00-11:00

    def test_adjacent_times_allowed(self):
        self._enroll(self.c1)  # 08:30-10:30
        self._enroll(self.c2)  # 10:30-12:30，首尾相接不算冲突
        self.assertEqual(self.db.query(models.Enrollment).count(), 2)

    def test_different_day_allowed(self):
        self._enroll(self.c1)  # 星期一
        self._enroll(self.c3)  # 星期二
        self.assertEqual(self.db.query(models.Enrollment).count(), 2)

    def test_drop_course(self):
        self._enroll(self.c1)
        result = drop(self.s1.id, self.c1.id, self.db, self.u1)
        self.assertEqual(result["message"], "退课成功")
        self.assertEqual(self.db.query(models.Enrollment).count(), 0)

    def test_enrolled_count_uses_sql_aggregation(self):
        self._enroll(self.c1)
        self._enroll(self.c1, student=self.s2, user=self.u2)
        self.db.expire_all()
        course = self.db.get(models.Course, self.c1.id)
        self.assertEqual(course.enrolled_count, 2)

    def test_foreign_key_is_enforced(self):
        self.db.add(models.Enrollment(student_id=999999, course_id=self.c1.id))
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()

    def test_keyword_search_matches_major_name(self):
        page = list_students(page=1, page_size=10, keyword="数据科学", db=self.db)
        self.assertEqual(page["total"], 2)

    def test_update_student_keeps_major_name_and_code_consistent(self):
        payload = schemas.StudentCreate(
            student_no=self.s1.student_no, name=self.s1.name, major="计算机科学",
            email=self.s1.email, age=self.s1.age, grade=self.s1.grade,
            major_code="013", gender=self.s1.gender, id_card=self.s1.id_card,
        )
        updated = update_student(self.s1.id, payload, self.db)
        self.assertEqual(updated.major_code, "014")
        self.assertEqual(updated.major, "计算机科学")

    def test_course_time_must_be_two_hours(self):
        payload = schemas.CourseCreate(
            course_code="T001", name="测试课程", credit=3, capacity=10,
            teacher="王老师", major="数据科学", day="星期一", period="上午",
            start_time="08:30", end_time="10:30", weeks="第1-13周",
        )
        created = create_course(payload, self.db, self.u1)
        self.assertEqual(created.end_time, "10:30")

        bad = payload.model_copy(update={"course_code": "T002", "end_time": "10:00"})
        with self.assertRaises(HTTPException) as ctx:
            create_course(bad, self.db, self.u1)
        self.assertIn("2 小时", ctx.exception.detail)

    def test_unknown_major_rejected(self):
        payload = schemas.StudentCreate(
            student_no="2022999999", name="王五", major="不存在的专业",
            email="2022999999@1.com", age=20, grade="2022",
            major_code="", gender="男", id_card="110101200001010033",
        )
        with self.assertRaises(HTTPException) as ctx:
            create_student(payload, self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("未知专业", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
