-- ============================================================
-- Student Course Registration System -- sample queries
-- 适用于 backend/students.db（SQLite），也适用于 schema.sql 新建的库。
-- 这些查询可直接用于报告 "Database Design -> Sample Queries" 一节。
-- ============================================================


-- 1) 课程容量、已选人数与剩余名额（LEFT JOIN + COUNT + GROUP BY）
SELECT c.course_code,
       c.name,
       c.major,
       c.capacity,
       COUNT(e.id)                  AS enrolled,
       c.capacity - COUNT(e.id)     AS remaining
FROM courses c
LEFT JOIN enrollments e ON e.course_id = c.id
GROUP BY c.id, c.course_code, c.name, c.major, c.capacity
ORDER BY enrolled DESC, c.course_code
LIMIT 20;


-- 2) 某个学生的课表（三表连接 + 按上课时间排序）
--    学号可替换为库中任意有选课记录的学生
SELECT s.student_no,
       s.name,
       c.course_code,
       c.name       AS course_name,
       c.day,
       c.start_time,
       c.end_time,
       c.weeks
FROM students s
JOIN enrollments e ON e.student_id = s.id
JOIN courses c     ON c.id = e.course_id
WHERE s.student_no = '2022013738'
ORDER BY c.day, c.start_time;


-- 3) 各专业学生人数与平均年龄（连接 majors 字典表）
SELECT m.code,
       m.name                        AS major,
       COUNT(s.id)                   AS student_count,
       ROUND(AVG(s.age), 1)          AS avg_age
FROM majors m
LEFT JOIN students s ON s.major_code = m.code
GROUP BY m.code, m.name
ORDER BY student_count DESC;


-- 4) 选课人数最多的 10 门课程（INNER JOIN + COUNT + ORDER BY + LIMIT）
SELECT c.course_code,
       c.name,
       COUNT(e.id) AS enrolled
FROM courses c
JOIN enrollments e ON e.course_id = c.id
GROUP BY c.id, c.course_code, c.name
ORDER BY enrolled DESC, c.course_code
LIMIT 10;


-- 5) 每位学生的选课数与计入总学分（体育/英语不计入）
SELECT s.student_no,
       s.name,
       COUNT(e.id) AS course_count,
       COALESCE(SUM(CASE WHEN c.major NOT IN ('体育', '英语')
                         THEN c.credit ELSE 0 END), 0) AS counted_credits
FROM students s
LEFT JOIN enrollments e ON e.student_id = s.id
LEFT JOIN courses c     ON c.id = e.course_id
GROUP BY s.id, s.student_no, s.name
HAVING COUNT(e.id) > 0
ORDER BY counted_credits DESC, course_count DESC
LIMIT 20;


-- 6) 尚未选任何课程的学生（NOT EXISTS 反连接）
SELECT s.student_no,
       s.name,
       m.name AS major
FROM students s
JOIN majors m ON m.code = s.major_code
WHERE NOT EXISTS (
    SELECT 1
    FROM enrollments e
    WHERE e.student_id = s.id
)
ORDER BY s.student_no
LIMIT 20;


-- 7) 修完本专业全部课程的学生（关系除法，双重 NOT EXISTS）
SELECT s.student_no,
       s.name,
       m.name AS major
FROM students s
JOIN majors m ON m.code = s.major_code
WHERE EXISTS (
          SELECT 1 FROM courses c2 WHERE c2.major = m.name
      )
  AND NOT EXISTS (
          SELECT 1
          FROM courses c
          WHERE c.major = m.name
            AND NOT EXISTS (
                    SELECT 1
                    FROM enrollments e
                    WHERE e.student_id = s.id
                      AND e.course_id = c.id
                )
      )
ORDER BY s.student_no;


-- 8) 容量告警：已选人数达到容量 80% 及以上的课程
SELECT c.course_code,
       c.name,
       c.capacity,
       COUNT(e.id) AS enrolled,
       ROUND(COUNT(e.id) * 100.0 / c.capacity, 1) AS pct
FROM courses c
LEFT JOIN enrollments e ON e.course_id = c.id
GROUP BY c.id, c.course_code, c.name, c.capacity
HAVING COUNT(e.id) >= 0.8 * c.capacity
ORDER BY pct DESC;
