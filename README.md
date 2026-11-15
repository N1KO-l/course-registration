# 学生选课系统（Student Course Registration System）

一个前后端分离的学生选课系统，支持老师批量导入学生、课程管理、选课/退课（含规则校验）、学生课表查看、JWT 登录与角色权限控制。

> 技术栈：FastAPI + Vue 3 + Element Plus + SQLite

---

## 目录

1. [项目简介](#项目简介)
2. [功能特性](#功能特性)
3. [技术栈](#技术栈)
4. [系统架构](#系统架构)
5. [数据库设计](#数据库设计)
6. [API 接口文档](#api-接口文档)
7. [核心业务规则](#核心业务规则)
8. [角色与权限](#角色与权限)
9. [快速开始](#快速开始)
10. [默认账号](#默认账号)
11. [批量导入学生](#批量导入学生)
12. [项目结构](#项目结构)
13. [技术要点](#技术要点)

---

## 项目简介

本系统是一个面向高校的选课系统，实现了「老师 - 学生」两种角色下的完整选课流程：

- **老师**：批量导入/管理学生、管理课程（含上课时间）、查看和修改任意学生的选课情况、批量删除学生、重置学生密码。
- **学生**：使用学号或邮箱登录，浏览可选课程、选课/退课、查看自己的课表、修改自己的密码。

系统内置了真实的选课规则（专业限制、学分上限、公共课/体育课数量限制、容量校验等），贴近真实高校选课场景。

---

## 功能特性

- **登录认证**：JWT 令牌 + 密码哈希（PBKDF2），支持「学号 / 邮箱 / 用户名」三种方式登录。
- **角色权限（RBAC）**：`teacher`（老师，最高权限）与 `student`（学生，仅选课）两种角色。
- **学生管理**：增删改查、按姓名/学号/专业搜索、分页、批量删除（含全选）。
- **批量导入学生**：支持「文本粘贴」和「Excel 上传」两种方式，自动生成学号、邮箱、初始密码。
- **课程管理**：增删改查、按专业筛选、按课程名/代码搜索、分页、编辑上课时间。
- **选课/退课**：多维度规则校验（专业、学分、公共课/体育课数量、容量、重复选课）。
- **学生课表**：按「小时」划分的周课表（横轴星期、纵轴时刻），课程按起止时间自动排布。
- **密码管理**：学生自行修改密码（需验证原密码）、老师重置任意学生密码。
- **分页搜索**：学生列表为后端分页（可扩展），课程列表为前端分页。

---

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端框架 | FastAPI | Python 异步 Web 框架，自带 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 | 数据库映射 |
| 数据库 | SQLite | 零配置，本地文件存储 |
| 认证 | PyJWT | JWT 令牌签发与校验 |
| 密码哈希 | hashlib（PBKDF2） | 标准库，加盐哈希 |
| Excel 解析 | openpyxl | 批量导入 Excel |
| 文件上传 | python-multipart | FastAPI 处理上传文件 |
| 前端框架 | Vue 3 | Composition API |
| 构建工具 | Vite | 开发服务器 + 打包 |
| UI 组件 | Element Plus | 表格、表单、弹窗、分页等 |
| HTTP 客户端 | Axios | 请求封装 + 拦截器 |

---

## 系统架构

```
浏览器（Vue 3 + Element Plus）
        │  HTTP（/api/*，Vite 开发代理转发到 8000）
        ▼
FastAPI 后端（端口 8000）
   ├── 路由层 routers/（auth / students / courses / enrollments）
   ├── 认证层 auth.py（JWT 签发、校验、角色依赖）
   ├── 数据层 models.py + SQLAlchemy
   └── SQLite 数据库（backend/students.db）
```

- 前端开发时通过 Vite 的 `/api` 代理转发到后端 `http://localhost:8000`，避免跨域。
- 后端通过 `CORSMiddleware` 允许 `http://localhost:5173` 访问（备用）。

---

## 数据库设计

### 表结构总览

共 5 张表：`majors`（专业字典）、`students`（学生）、`courses`（课程）、`enrollments`（选课关系）、`users`（登录账号）。

完整 DDL 见 [`backend/schema.sql`](backend/schema.sql)。

### majors（专业字典表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| code | String | 主键 | 三位专业代码（如 013）|
| name | String | 唯一、非空 | 专业名称（如 数据科学）|

> 拆分出该表是为了消除 `students` 中 `major → major_code` 的传递依赖，使 `students` 达到 3NF。

### students（学生表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键 | 自增 |
| student_no | String | 唯一 | 学号（自动生成：年级+专业代码+随机3位）|
| name | String | | 姓名（可重名）|
| email | String | | 邮箱（自动生成：学号@1.com）|
| age | Integer | | 年龄 |
| grade | String | | 年级（如 2022）|
| major_code | String | 外键 → majors.code | 三位专业代码（如 013）|
| gender | String | | 性别（男/女）|
| id_card | String | 唯一 | 身份证号（18 位）|

> 专业名称不再冗余存储在 `students` 中，由 `majors` 表连接得到（`Student.major` 为只读属性）。

### courses（课程表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键 | 自增 |
| course_code | String | 唯一 | 课程代码（如 DSC5001）|
| name | String | | 课程名称 |
| credit | Integer | | 学分 |
| capacity | Integer | | 容量（人数上限）|
| teacher | String | | 教师 |
| major | String | | 所属专业（公共课/体育/英语为特殊类别）|
| day | String | | 星期几（如 星期一）|
| period | String | | 时间段（上午/下午/晚上）|
| start_time | String | | 开始时间（如 14:00）|
| end_time | String | | 结束时间（如 16:00）|
| weeks | String | | 周次（如 第1-13周）|

> 课程数据共 **200 门**：67 门主课程 + 133 门扩展示例课程，容量统一为 **50**。
> `seed.py` 为每门课分配任课教师和 **2 小时** 上课时段（上午 08:30–10:30、
> 下午 14:00–16:00、晚上 19:00–21:00）；每个专业都有 15 个不同时段可选，
> 便于学生组合出 5 门不冲突的课程。

### enrollments（选课关系表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键 | 自增 |
| student_id | Integer | 外键 → students.id | 学生 |
| course_id | Integer | 外键 → courses.id | 课程 |
| enrolled_at | DateTime | | 选课时间 |

> 联合唯一约束 `(student_id, course_id)`，保证同一学生不能重复选同一门课。

### users（登录账号表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键 | 自增 |
| username | String | 唯一 | 登录账号（学生为学号，老师为自定义）|
| hashed_password | String | | 密码哈希 |
| role | String | | 角色：teacher / student |
| student_id | Integer | 外键 → students.id，可空 | 关联学生（学生角色时非空）|

### 表关系

```
majors   1 ── N students
students 1 ── N enrollments N ── 1 courses
users    1 ── 1 students（学生角色的登录账号）
```

- 删除学生时，级联删除其选课记录和登录账号。
- 删除课程时，级联删除相关的选课记录。
- 外键通过 `app/database.py` 的 `connect` 事件对每个 SQLite 连接执行
  `PRAGMA foreign_keys=ON`，由数据库强制参照完整性。

### 规范化级别

- `majors(code, name)`：`code` 为主键，`name` 为候选键（BCNF）。
- `students`：候选键为 `id`、`student_no`、`id_card`；专业名称已移出，消除了
  `major → major_code` 传递依赖，达到 **3NF**。
- `courses`：`id` / `course_code` 为候选键，非主属性之间无函数依赖，达到 3NF。
- `enrollments`：`id` 为主键，`(student_id, course_id)` 为唯一约束，达到 BCNF。
- `users`：`id` / `username` 为候选键，达到 3NF。
- `Course.enrolled_count` 是派生值，不落库，由 `COUNT` 聚合实时计算，避免冗余。

### 索引策略

| 索引 | 用途 |
|------|------|
| `ix_students_student_no`（唯一） | 学号登录 / 按学号查找 |
| `ix_students_name` | 按姓名搜索 |
| `ix_students_major_code` | 按专业筛选、majors 连接 |
| `ix_students_id_card`（唯一约束） | 身份证号去重 |
| `ix_courses_course_code`（唯一） | 课程代码查找 |
| `ix_courses_name` | 按课程名搜索 |
| `ix_courses_major` | 按专业筛选课程 |
| `ix_enrollments_course_id` | 统计某课程选课人数 / 容量校验 |
| `uq_student_course`（唯一） | 防重复选课，同时服务 student_id 前缀查询 |
| `ix_users_username`（唯一） | 登录账号查找 |
| `ix_users_student_id` | 账号 ↔ 学生关联 |

> 说明：`LIKE '%关键字%'` 是前缀通配，无法使用 B-Tree 索引；数据量大时应改用
> FTS5 全文索引，本项目数据规模（5000 学生）下扫描耗时仍低于 1 ms。

---

## API 接口文档

所有接口（除登录外）都需要在请求头携带 JWT：`Authorization: Bearer <token>`。

### 认证接口（/api/auth）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | /api/auth/login | 公开 | 登录 |
| POST | /api/auth/batch-register | 老师 | 批量注册学生（JSON）|
| POST | /api/auth/import-excel | 老师 | 批量导入学生（Excel 上传）|
| GET | /api/auth/me | 登录用户 | 获取当前用户信息 |
| POST | /api/auth/change-password | 登录用户 | 修改自己的密码 |

**POST /api/auth/login** — 登录

请求体：
```json
{ "account": "2022013052", "password": "123456" }
```
`account` 可以是用户名、学号或邮箱。

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "username": "2022013052",
  "role": "student",
  "student_id": 1,
  "major": "数据科学",
  "name": "张三"
}
```

**POST /api/auth/batch-register** — 批量注册（文本导入）

请求体：
```json
{
  "students": [
    { "name": "张三", "grade": "2022", "major": "数据科学", "age": 22, "gender": "男", "id_card": "110101200401010011" }
  ]
}
```

响应：
```json
{
  "created_count": 1,
  "created": [ { "student_no": "2022013052", "name": "张三", "email": "2022013052@1.com" } ],
  "skipped": []
}
```

**POST /api/auth/import-excel** — Excel 导入

`multipart/form-data`，字段名 `file`，文件为 `.xlsx` 或 `.xls`。第一行为表头，列顺序：姓名、年级、专业、年龄、性别、身份证号。

**POST /api/auth/change-password** — 修改密码

请求体：
```json
{ "old_password": "123456", "new_password": "abc123" }
```

### 学生接口（/api/students，老师权限）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/students/ | 老师 | 分页列表（page、page_size、keyword）|
| POST | /api/students/ | 老师 | 新增学生 |
| GET | /api/students/{id} | 老师 | 学生详情 |
| PUT | /api/students/{id} | 老师 | 更新学生 |
| DELETE | /api/students/{id} | 老师 | 删除学生（含账号）|
| POST | /api/students/batch-delete | 老师 | 批量删除 |
| POST | /api/students/{id}/reset-password | 老师 | 重置密码 |

**GET /api/students/** — 分页列表

查询参数：`page`（页码，默认 1）、`page_size`（每页条数，默认 10，最大 10000）、`keyword`（关键字，匹配姓名/学号/专业）。

响应：
```json
{
  "total": 5000,
  "items": [
    { "id": 1, "student_no": "2022013052", "name": "张三", "major": "数据科学", "email": "2022013052@1.com", "age": 22, "grade": "2022", "major_code": "013", "gender": "男", "id_card": "110101200401010011" }
  ]
}
```

**POST /api/students/batch-delete** — 批量删除

请求体：
```json
{ "ids": [1, 2, 3] }
```
响应：
```json
{ "deleted_count": 3 }
```

### 课程接口（/api/courses）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/courses/ | 登录用户 | 课程列表（全量）|
| POST | /api/courses/ | 老师 | 新增课程 |
| GET | /api/courses/{id} | 老师 | 课程详情 |
| PUT | /api/courses/{id} | 老师 | 更新课程 |
| DELETE | /api/courses/{id} | 老师 | 删除课程 |

**GET /api/courses/** 响应（含 `enrolled_count` 已选人数）：
```json
[
  {
    "id": 1,
    "course_code": "DSC5001",
    "name": "统计机器学习 I",
    "credit": 3,
    "capacity": 50,
    "teacher": "",
    "major": "数据科学",
    "day": "星期一",
    "period": "下午",
    "start_time": "14:00",
    "end_time": "15:50",
    "weeks": "第1-13周",
    "enrolled_count": 12
  }
]
```

### 选课接口（/api/students/{student_id}/courses）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | /api/students/{student_id}/courses | 老师或本人 | 已选课程列表 |
| POST | /api/students/{student_id}/courses | 老师或本人 | 选课 |
| DELETE | /api/students/{student_id}/courses/{course_id} | 老师或本人 | 退课 |

**POST 选课** 请求体：
```json
{ "course_id": 1 }
```
成功响应：
```json
{ "ok": true, "message": "选课成功" }
```
失败响应（违反规则）：
```json
{ "detail": "总学分不能超过 17 学分" }
```

---

## 核心业务规则

选课接口会依次校验以下规则，违反时返回 400 和具体原因：

1. **只能选本专业课程**：课程专业必须与学生专业一致（公共课、体育、英语除外）。
2. **最多选 5 门课**：每名学生的选课总数不超过 5 门。
3. **上课时间不能冲突**：同一名学生已选课程中，同一天且时间区间重叠的课程不能同时选择；单次课程统一为 2 小时。
4. **公共课最多 1 门**：思政类公共课（IP5901/IP5902）最多选一门。
5. **体育课最多 1 门**：体育课（PE5911/PE6911）最多选一门。
6. **总学分不超过 17**：已选课程（体育、英语不计入）总学分 + 新课程学分 ≤ 17。
7. **容量校验**：课程已满（已选人数 ≥ 容量）时不可选。
8. **重复选课校验**：同一学生不能重复选同一门课。

> 体育、英语类课程不计入总学分。相关常量定义在 `backend/app/routers/enrollments.py`：
> `COMMON_MAJOR = "公共课"`、`PE_MAJOR = "体育"`、`FREE_ELECTIVE_MAJORS = {"体育", "英语"}`、
> `MAX_CREDITS = 17`、`MAX_COURSES = 5`。

### 学号生成规则

学号 = 年级（4 位）+ 专业代码（3 位）+ 随机 3 位，共 10 位。随机部分自动查重，保证唯一。

例如：`2022` + `013` + `217` = `2022013217`。

专业代码映射在 `backend/app/majors.py`：

| 专业 | 代码 |
|------|------|
| 工程管理 | 010 |
| 电子电气工程 | 011 |
| 电子信息工程 | 012 |
| 数据科学 | 013 |
| 计算机科学 | 014 |
| 人工智能 | 015 |
| 材料工程与纳米技术 | 016 |
| 生物医学工程 | 017 |
| 商业数据分析 | 018 |
| 商业信息系统 | 019 |
| 创业管理 | 020 |

> ⚠️ 以上专业代码为占位默认值，请按学校实际编码修改 `majors.py`。

---

## 角色与权限

| 操作 | 老师 | 学生 |
|------|------|------|
| 登录 | ✅ | ✅ |
| 学生增删改查 / 批量导入 / 批量删除 | ✅ | ❌ |
| 重置学生密码 | ✅ | ❌ |
| 课程增删改 | ✅ | ❌ |
| 查看课程列表 | ✅ | ✅ |
| 选课 / 退课 | ✅（任意学生）| ✅（仅自己）|
| 查看自己课表 | — | ✅ |
| 修改自己密码 | ✅ | ✅ |

权限实现：JWT 中携带 `role` 字段，后端通过 `get_current_user` 和 `require_teacher` 两个依赖控制。

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 1. 启动后端（端口 8000）

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 初始化数据库（建表、写入 majors、导入 200 门课程、创建默认账号）
.venv/bin/python seed.py

# 如果使用旧版数据库（students 表还有 major 列），先执行规范化迁移
# 脚本会自动备份为 students.db.bak-时间戳
.venv/bin/python scripts/migrate_normalize.py

# 可选：生成可复现的测试数据（学生 / 账号 / 选课）
# 生成时自动遵守 5 门上限、上课时间冲突、容量等规则；
# 做压力测试时可加 --ignore-capacity
.venv/bin/python scripts/generate_data.py --students 5000 --enrollments 20000 --seed 42 --ignore-capacity

# 可选：不新增学生，只给库里已有学生补充演示选课记录
.venv/bin/python scripts/generate_data.py --students 0 --enrollments 2000 --seed 42 --enroll-existing

# 清理历史选课数据，使其满足 5 门上限 / 时间冲突 / 学分等规则
# 可先加 --dry-run 只统计不删除
.venv/bin/python scripts/normalize_enrollments.py --dry-run
.venv/bin/python scripts/normalize_enrollments.py

# 运行单元测试
.venv/bin/python -m unittest discover -s tests -v

# 查询基准测试 + SQLite 查询计划
.venv/bin/python scripts/benchmark.py

.venv/bin/uvicorn app.main:app --reload --port 8000
```

启动后访问 http://localhost:8000/docs 查看交互式 API 文档。

> 可通过环境变量 `DATABASE_URL` 指向其它数据库文件，例如
> `DATABASE_URL=sqlite:////tmp/demo.db .venv/bin/python seed.py`。

### 2. 启动前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173。

### 3. 登录

用默认账号登录，详见下一节。

---

## 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 老师 | `teacher` | `teacher123` |
| 老师（兼容）| `admin` | `admin123` |
| 学生 | 学号 或 学号@1.com | `123456`（初始密码）|

> 学生的初始密码统一为 `123456`，登录后可自行修改。

---

## 批量导入学生

### 文本导入（粘贴）

每行一个学生，格式：`姓名,年级,专业,年龄,性别,身份证号`

```
张三,2022,数据科学,22,男,110101200401010011
李四,2022,数据科学,21,女,110101200401010023
```

### Excel 导入

`.xlsx` 文件，第一行为表头，列顺序与文本一致：

| 姓名 | 年级 | 专业 | 年龄 | 性别 | 身份证号 |
|------|------|------|------|------|---------|
| 张三 | 2022 | 数据科学 | 22 | 男 | 110101200401010011 |

### 自动生成

- **学号**：年级 + 专业代码 + 随机 3 位（自动查重）。
- **邮箱**：`学号@1.com`。
- **初始密码**：`123456`。
- **登录账号**：用户名 = 学号。

### 校验规则

- 姓名/年级/专业不能为空。
- 专业必须在 `majors.py` 的映射中存在。
- 身份证号为 18 位（前 17 位数字，末位数字或 X），且不能重复。

---

## 项目结构

```
course-registration/
├── backend/                      # 后端（FastAPI）
│   ├── app/
│   │   ├── main.py               # 应用入口、CORS、路由注册、建表
│   │   ├── database.py           # 数据库连接、Session、Base
│   │   ├── models.py             # 数据模型（Student/Course/Enrollment/User）
│   │   ├── schemas.py            # Pydantic 校验模型
│   │   ├── auth.py               # 密码哈希、JWT 签发校验、权限依赖
│   │   ├── majors.py             # 专业代码映射
│   │   └── routers/
│   │       ├── auth.py           # 登录、批量注册、Excel 导入、改密码
│   │       ├── students.py       # 学生 CRUD、批量删除、重置密码
│   │       ├── courses.py        # 课程 CRUD
│   │       └── enrollments.py    # 选课/退课（含规则校验）
│   ├── seed.py                   # 初始化脚本（建表、majors、导入课程、创建账号）
│   ├── schema.sql                # 规范化后的完整建表 DDL（含索引）
│   ├── sample_queries.sql        # 报告用示例查询（连接/聚合/反连接/除法）
│   ├── scripts/
│   │   ├── migrate_normalize.py  # 旧库迁移：新增 majors、删除 students.major
│   │   ├── generate_data.py      # 可复现的测试数据生成器（遵守选课规则）
│   │   ├── normalize_enrollments.py  # 清理不满足 5 门/时间冲突等规则的历史选课
│   │   └── benchmark.py          # 关键查询基准测试 + EXPLAIN QUERY PLAN
│   ├── tests/
│   │   └── test_enrollment_rules.py  # 选课规则（含 5 门/时间冲突）/ 外键 / 聚合测试
│   ├── requirements.txt          # 后端依赖
│   └── students.db               # SQLite 数据库文件（运行后生成）
├── frontend/                     # 前端（Vue 3 + Vite）
    ├── public/
    │   ├── logo.png              # 校徽（登录页，深色底用）
    │   └── logo-header.png       # 校徽（头部，浅色底用）
    ├── src/
    │   ├── main.js               # 入口，注册 Element Plus + 中文语言
    │   ├── App.vue               # 根组件、角色导航、头部/页脚
    │   ├── api/
    │   │   ├── http.js           # Axios 实例 + 拦截器（自动带 token、401 跳转）
    │   │   ├── auth.js           # 登录、批量注册、Excel 导入、改密码
    │   │   ├── students.js       # 学生接口
    │   │   ├── courses.js        # 课程接口
    │   │   └── enrollments.js    # 选课接口
    │   └── views/
    │       ├── Login.vue         # 登录页
    │       ├── Students.vue      # 学生管理（老师）
    │       ├── Courses.vue       # 课程管理（老师）
    │       ├── Enrollments.vue   # 选课/退课（老师）
    │       ├── StudentEnroll.vue # 学生选课页
    │       └── StudentTimetable.vue # 学生课表页
    ├── vite.config.js            # Vite 配置（含 /api 代理）
    ├── index.html
    └── package.json
├── er-diagram.drawio             # ER 图 + 系统架构图（两个 page）
├── er-diagram.svg / .png         # ER 图导出（报告用）
└── system-architecture.svg / .png # 系统架构图导出（报告用）
```

---

## 技术要点

### 数据库与查询

- **参照完整性**：`database.py` 在每次 SQLite 连接时开启 `PRAGMA foreign_keys=ON`，
  外键由数据库强制，而不是只做声明。
- **规范化**：专业名称拆分到 `majors` 表，`students` 只保留 `major_code` 外键，
  消除传递依赖，达到 3NF（详见「数据库设计」）。
- **SQL 聚合**：`Course.enrolled_count` 用相关子查询 `COUNT(*)` 实现
  （`column_property`），列表页一次查询即可拿到已选人数，避免 N+1。
- **索引**：为外键和常用筛选列建立索引，`benchmark.py` 的
  `EXPLAIN QUERY PLAN` 可验证查询确实走了索引。
- **可复现数据**：`generate_data.py` 固定随机种子生成学生、账号和选课记录。
- **测试**：`tests/` 覆盖重复选课、容量、专业限制、学分上限、公共课/体育限选、
  外键约束、聚合计数与专业一致性。

### 基准测试结果（本机示例）

数据量：5000 名学生、20000 条选课记录（`generate_data.py --students 5000
--enrollments 20000 --ignore-capacity`）。具体数值随机器变化。

| 查询 | 平均耗时 |
|------|---------|
| 分页：第 1 页 (LIMIT 20) | 0.13 ms |
| 分页：最后一页 (OFFSET 4980) | 0.14 ms |
| 关键字搜索 `LIKE '%王%'`（含专业名） | 0.92 ms |
| 每门课已选人数 `COUNT + GROUP BY` | 0.76 ms |
| 课程列表 + `enrolled_count` 相关子查询 | 0.51 ms |
| 按课程查选课记录（`course_id` 索引） | 0.38 ms |

`EXPLAIN QUERY PLAN` 显示按课程统计走 `ix_enrollments_course_id`，按专业
连接走 `ix_students_major_code` / `ix_courses_major`，均未全表扫描。

### 示例查询与图表

- `backend/sample_queries.sql`：8 条代表性查询，覆盖多表连接、`GROUP BY`
  统计、`NOT EXISTS` 反连接和关系除法，可直接用于报告。
- `er-diagram.drawio`：draw.io 源文件，含 **ER Diagram** 和
  **System Architecture** 两个 page。
- `er-diagram.svg` / `er-diagram.png`、`system-architecture.svg` /
  `system-architecture.png`：已导出的报告用图片。

### 认证与权限

- 密码使用 `hashlib.pbkdf2_hmac`（SHA-256，10 万次迭代）加盐哈希存储，不存明文。
- JWT 使用 `PyJWT`，HS256 算法，有效期 1 天，payload 含 `sub`（用户名）和 `role`（角色）。
- `get_current_user` 依赖：校验 token 并返回当前用户。
- `require_teacher` 依赖：校验当前用户是否为老师，否则返回 403。
- 选课接口额外校验「老师或本人」：学生只能操作自己的选课。

### 前端请求封装

- `api/http.js` 使用 Axios 拦截器：
  - 请求拦截：自动从 `localStorage` 读取 token 并加到 `Authorization` 头。
  - 响应拦截：遇到 401 时清除本地 token 并刷新页面，跳回登录。
- 登录成功后，把 `token`、`role`、`student_id`、`name`、`major` 存入 `localStorage`。

### 分页搜索

- 学生列表为**后端分页**：`GET /api/students/?page=&page_size=&keyword=`，返回 `{total, items}`。
- 课程列表为**前端分页**：前端一次性加载全量课程，本地过滤分页（课程数据量小且固定）。

### 课表展示

- 课表按「小时」划分（8:00 ~ 20:00），横轴星期、纵轴时刻。
- 前端根据课程的 `day` + `start_time` + `end_time` 计算其在网格中的位置，用 `rowspan` 实现跨小时单元格。

---

## 说明

- 本项目的专业代码、课程时间、课程数据等均为示例/占位数据，请按学校实际情况修改 `backend/app/majors.py` 和 `backend/seed.py`。
- 生产环境应将 `SECRET_KEY`（`backend/app/auth.py`）改为环境变量，并使用更健壮的数据库（如 PostgreSQL）。
