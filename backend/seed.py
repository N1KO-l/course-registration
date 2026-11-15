# -*- coding: utf-8 -*-
"""导入课程数据：67 门主课程 + 133 门扩展示例课程，共 200 门。

主课程数据来源：《Course List of Semester A 2026/27 for TPg Year1 Students》；
扩展课程为示例数据，容量统一为 50，并自动分配教师和 2 小时时段。

用法：cd backend && .venv/bin/python seed.py
可重复运行，已存在的课程代码会被更新（幂等）。
"""
from sqlalchemy import inspect, text

from app import models
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.majors import MAJOR_CODES

# (课程代码, 课程名称, 学分, 专业)
COURSES = [
    # 工程管理
    ("SYE5006", "运营管理", 3, "工程管理"),
    ("SYE5010", "工程管理原理与概念", 3, "工程管理"),
    ("SYE6043", "质量与可靠性工程", 3, "工程管理"),
    ("SYE6037", "战略质量管理", 3, "工程管理"),
    ("SYE6045", "工业案例研究", 3, "工程管理"),
    ("SYE6106", "工程经理智能制造", 3, "工程管理"),
    ("SYE6107", "现代职业安全与健康管理", 3, "工程管理"),
    ("SYE6302", "设计科学", 3, "工程管理"),
    # 电子电气 / 电子信息
    ("EE5415", "移动应用设计与开发", 3, "电子电气工程"),
    ("EE5425", "射频电路工程基础", 3, "电子电气工程"),
    ("EE5430", "高级CMOS技术", 3, "电子电气工程"),
    ("EE5436", "光子学基础与应用", 3, "电子信息工程"),
    ("EE5606", "无线通信天线人工智能", 3, "电子电气工程"),
    ("EE6427", "现代电力电子", 3, "电子信息工程"),
    ("EE6603", "无线通信技术", 3, "电子信息工程"),
    ("EE6605", "复杂网络：建模、动力学与控制", 3, "电子信息工程"),
    ("EE6622", "智能电网专题", 3, "电子电气工程"),
    ("EE8405", "排队论及其电信应用", 3, "电子信息工程"),
    # 数据科学
    ("DSC5001", "统计机器学习 I", 3, "数据科学"),
    ("DSC5002", "探索性数据分析与可视化", 3, "数据科学"),
    ("DSC5003", "数据存储与检索", 3, "数据科学"),
    ("DSC6003", "贝叶斯数据分析", 3, "数据科学"),
    ("DSC6004", "智慧城市人工智能专题", 3, "数据科学"),
    ("DSC6011", "数据科学优化", 3, "数据科学"),
    ("DSC8011", "数据科学社会基础", 3, "数据科学"),
    # 计算机科学
    ("CS5185", "多媒体技术与应用", 3, "计算机科学"),
    ("CS5285", "电子商务信息安全", 3, "计算机科学"),
    ("CS5351", "软件工程", 3, "计算机科学"),
    ("CS5481", "数据工程", 3, "计算机科学"),
    ("CS6382", "算法分析与博弈论", 3, "计算机科学"),
    ("CS5487", "机器学习：原理与实践", 3, "计算机科学"),
    # 人工智能
    ("CS5187", "视觉与图像", 3, "人工智能"),
    ("CS5486", "智能系统", 3, "人工智能"),
    ("CS5489", "机器学习：算法与应用", 3, "人工智能"),
    ("CS5491", "人工智能", 3, "人工智能"),
    ("DSC6007", "动态规划与强化学习", 3, "数据科学"),
    # 材料工程与纳米技术
    ("MSE5301", "材料表征仪器", 3, "材料工程与纳米技术"),
    ("MSE5304", "材料热力学", 3, "材料工程与纳米技术"),
    ("MSE6121", "薄膜技术与纳米晶涂层", 3, "材料工程与纳米技术"),
    ("MSE6176", "能源应用纳米材料设计", 3, "材料工程与纳米技术"),
    ("MSE6183", "材料科学计算方法", 3, "材料工程与纳米技术"),
    ("MSE6602", "高级散射技术", 3, "材料工程与纳米技术"),
    ("MSE6603", "材料科学人工智能", 3, "材料工程与纳米技术"),
    # 生物医学工程
    ("BME6111", "生物医学仪器", 3, "生物医学工程"),
    ("BME6118", "生物医学成像与生物光子学", 3, "生物医学工程"),
    ("BME6123", "医疗应用柔性生物电子", 3, "生物医学工程"),
    ("BME6135", "药物递送工程原理", 3, "生物医学工程"),
    ("BME6144", "生物芯片设计与应用", 3, "生物医学工程"),
    ("BME6145", "生物医学与医疗健康应用人工智能", 3, "生物医学工程"),
    # 商业数据分析 / 商业信息系统
    ("IS5312", "Python分析编程", 3, "商业数据分析"),
    ("IS5313", "信息与电子商务系统基础", 3, "商业信息系统"),
    ("IS5413", "数据库管理系统", 3, "商业数据分析"),
    ("IS5540", "项目管理与质量保证", 3, "商业信息系统"),
    ("IS5740", "管理支持与商业智能系统", 3, "商业数据分析"),
    ("IS6335", "数据可视化", 3, "商业数据分析"),
    ("MS5217", "统计数据分析", 3, "商业数据分析"),
    # 创业管理
    ("AC5813", "财务与管理会计", 3, "创业管理"),
    ("IS6200", "区块链技术与商业应用", 3, "创业管理"),
    ("MGT6066", "商业伦理与社会责任", 3, "创业管理"),
    ("MKT5610", "营销战略与规划", 3, "创业管理"),
    ("MGT6325", "创业学", 3, "创业管理"),
    ("CAI6002", "创业创建研讨会", 3, "创业管理"),
    # 公共课
    ("IP5901", "新时代中国特色社会主义理论与实践", 2, "公共课"),
    ("IP5902", "自然辩证法概论", 1, "公共课"),
    ("EN1002P", "研究生英语强化课程", 3, "英语"),
    # 体育
    ("PE5911", "体育课 5A", 1, "体育"),
    ("PE6911", "体育课 6A", 1, "体育"),
]

# 扩展课程（示例数据）：把课程总数补充到 200 门
# 与 COURSES 分开定义，避免改变原有 67 门课程已分配的教师和时间
EXTRA_COURSES = [
    # 工程管理 +8
    ("SYE9001", "项目管理", 3, "工程管理"),
    ("SYE9002", "供应链管理", 3, "工程管理"),
    ("SYE9003", "工程经济学", 3, "工程管理"),
    ("SYE9004", "工程风险管理", 3, "工程管理"),
    ("SYE9005", "全面质量管理", 3, "工程管理"),
    ("SYE9006", "运筹学", 3, "工程管理"),
    ("SYE9007", "工程伦理", 3, "工程管理"),
    ("SYE9008", "创新创业管理", 3, "工程管理"),
    # 电子电气工程 +11
    ("EE9001", "电力系统分析", 3, "电子电气工程"),
    ("EE9002", "电机学", 3, "电子电气工程"),
    ("EE9003", "自动控制原理", 3, "电子电气工程"),
    ("EE9004", "电力电子技术", 3, "电子电气工程"),
    ("EE9005", "高电压技术", 3, "电子电气工程"),
    ("EE9006", "电气测量技术", 3, "电子电气工程"),
    ("EE9007", "继电保护", 3, "电子电气工程"),
    ("EE9008", "新能源发电技术", 3, "电子电气工程"),
    ("EE9009", "智能电网", 3, "电子电气工程"),
    ("EE9010", "电气工程实践", 3, "电子电气工程"),
    ("EE9011", "电力市场", 3, "电子电气工程"),
    # 电子信息工程 +11
    ("EIE9001", "信号与系统", 3, "电子信息工程"),
    ("EIE9002", "数字信号处理", 3, "电子信息工程"),
    ("EIE9003", "通信原理", 3, "电子信息工程"),
    ("EIE9004", "电磁场与电磁波", 3, "电子信息工程"),
    ("EIE9005", "微波技术", 3, "电子信息工程"),
    ("EIE9006", "天线原理", 3, "电子信息工程"),
    ("EIE9007", "射频电路", 3, "电子信息工程"),
    ("EIE9008", "嵌入式系统", 3, "电子信息工程"),
    ("EIE9009", "物联网技术", 3, "电子信息工程"),
    ("EIE9010", "信息论与编码", 3, "电子信息工程"),
    ("EIE9011", "电子系统设计", 3, "电子信息工程"),
    # 数据科学 +8
    ("DSC9001", "数据挖掘", 3, "数据科学"),
    ("DSC9002", "大数据技术", 3, "数据科学"),
    ("DSC9003", "数据可视化", 3, "数据科学"),
    ("DSC9004", "统计学基础", 3, "数据科学"),
    ("DSC9005", "机器学习基础", 3, "数据科学"),
    ("DSC9006", "深度学习", 3, "数据科学"),
    ("DSC9007", "数据伦理", 3, "数据科学"),
    ("DSC9008", "数据工程实践", 3, "数据科学"),
    # 计算机科学 +10
    ("CS9001", "操作系统", 3, "计算机科学"),
    ("CS9002", "计算机网络", 3, "计算机科学"),
    ("CS9003", "数据库系统", 3, "计算机科学"),
    ("CS9004", "编译原理", 3, "计算机科学"),
    ("CS9005", "软件工程", 3, "计算机科学"),
    ("CS9006", "计算机组成原理", 3, "计算机科学"),
    ("CS9007", "分布式系统", 3, "计算机科学"),
    ("CS9008", "网络安全", 3, "计算机科学"),
    ("CS9009", "算法设计", 3, "计算机科学"),
    ("CS9010", "云计算", 3, "计算机科学"),
    # 人工智能 +12
    ("AI9001", "知识表示", 3, "人工智能"),
    ("AI9002", "自然语言处理", 3, "人工智能"),
    ("AI9003", "计算机视觉", 3, "人工智能"),
    ("AI9004", "强化学习", 3, "人工智能"),
    ("AI9005", "智能机器人", 3, "人工智能"),
    ("AI9006", "模式识别", 3, "人工智能"),
    ("AI9007", "多智能体系统", 3, "人工智能"),
    ("AI9008", "生成式人工智能", 3, "人工智能"),
    ("AI9009", "联邦学习", 3, "人工智能"),
    ("AI9010", "图神经网络", 3, "人工智能"),
    ("AI9011", "人工智能伦理", 3, "人工智能"),
    ("AI9012", "智能系统实践", 3, "人工智能"),
    # 材料工程与纳米技术 +9
    ("MSE9001", "材料物理", 3, "材料工程与纳米技术"),
    ("MSE9002", "材料化学", 3, "材料工程与纳米技术"),
    ("MSE9003", "纳米材料", 3, "材料工程与纳米技术"),
    ("MSE9004", "复合材料", 3, "材料工程与纳米技术"),
    ("MSE9005", "材料成型工艺", 3, "材料工程与纳米技术"),
    ("MSE9006", "材料分析测试", 3, "材料工程与纳米技术"),
    ("MSE9007", "表面工程", 3, "材料工程与纳米技术"),
    ("MSE9008", "能源材料", 3, "材料工程与纳米技术"),
    ("MSE9009", "生物材料", 3, "材料工程与纳米技术"),
    # 生物医学工程 +10
    ("BME9001", "生物力学", 3, "生物医学工程"),
    ("BME9002", "生物材料", 3, "生物医学工程"),
    ("BME9003", "医学影像", 3, "生物医学工程"),
    ("BME9004", "生物信号处理", 3, "生物医学工程"),
    ("BME9005", "医疗器械设计", 3, "生物医学工程"),
    ("BME9006", "组织工程", 3, "生物医学工程"),
    ("BME9007", "神经工程", 3, "生物医学工程"),
    ("BME9008", "生物传感器", 3, "生物医学工程"),
    ("BME9009", "临床工程", 3, "生物医学工程"),
    ("BME9010", "生物医学工程实践", 3, "生物医学工程"),
    # 商业数据分析 +11
    ("IS9001", "商业统计", 3, "商业数据分析"),
    ("IS9002", "数据驱动决策", 3, "商业数据分析"),
    ("IS9003", "市场分析", 3, "商业数据分析"),
    ("IS9004", "财务分析", 3, "商业数据分析"),
    ("IS9005", "运营分析", 3, "商业数据分析"),
    ("IS9006", "客户分析", 3, "商业数据分析"),
    ("IS9007", "数据可视化", 3, "商业数据分析"),
    ("IS9008", "预测建模", 3, "商业数据分析"),
    ("IS9009", "商业智能", 3, "商业数据分析"),
    ("IS9010", "文本分析", 3, "商业数据分析"),
    ("IS9011", "商业数据实践", 3, "商业数据分析"),
    # 商业信息系统 +14
    ("ISB9001", "管理信息系统", 3, "商业信息系统"),
    ("ISB9002", "企业资源规划", 3, "商业信息系统"),
    ("ISB9003", "电子商务", 3, "商业信息系统"),
    ("ISB9004", "客户关系管理", 3, "商业信息系统"),
    ("ISB9005", "信息系统分析", 3, "商业信息系统"),
    ("ISB9006", "信息系统设计", 3, "商业信息系统"),
    ("ISB9007", "数据库管理", 3, "商业信息系统"),
    ("ISB9008", "信息安全", 3, "商业信息系统"),
    ("ISB9009", "业务流程管理", 3, "商业信息系统"),
    ("ISB9010", "数字化转型", 3, "商业信息系统"),
    ("ISB9011", "供应链信息系统", 3, "商业信息系统"),
    ("ISB9012", "信息系统项目管理", 3, "商业信息系统"),
    ("ISB9013", "系统实施", 3, "商业信息系统"),
    ("ISB9014", "信息系统实践", 3, "商业信息系统"),
    # 创业管理 +10
    ("MGT9001", "创业融资", 3, "创业管理"),
    ("MGT9002", "商业模式创新", 3, "创业管理"),
    ("MGT9003", "创业营销", 3, "创业管理"),
    ("MGT9004", "创业团队管理", 3, "创业管理"),
    ("MGT9005", "创业法律", 3, "创业管理"),
    ("MGT9006", "创业财务", 3, "创业管理"),
    ("MGT9007", "企业成长管理", 3, "创业管理"),
    ("MGT9008", "社会创业", 3, "创业管理"),
    ("MGT9009", "创业案例分析", 3, "创业管理"),
    ("MGT9010", "创业实践", 3, "创业管理"),
    # 公共课 +8
    ("IP9001", "思想道德与法治", 2, "公共课"),
    ("IP9002", "中国近现代史纲要", 2, "公共课"),
    ("IP9003", "马克思主义基本原理", 2, "公共课"),
    ("IP9004", "毛泽东思想和中国特色社会主义理论体系概论", 2, "公共课"),
    ("IP9005", "形势与政策", 2, "公共课"),
    ("IP9006", "习近平新时代中国特色社会主义思想概论", 2, "公共课"),
    ("IP9007", "军事理论", 2, "公共课"),
    ("IP9008", "大学生心理健康", 2, "公共课"),
    # 英语 +6
    ("EN9001", "学术英语写作", 3, "英语"),
    ("EN9002", "英语听说", 3, "英语"),
    ("EN9003", "英语阅读", 3, "英语"),
    ("EN9004", "科技英语", 3, "英语"),
    ("EN9005", "商务英语", 3, "英语"),
    ("EN9006", "跨文化交际", 3, "英语"),
    # 体育 +5
    ("PE9001", "篮球", 1, "体育"),
    ("PE9002", "足球", 1, "体育"),
    ("PE9003", "羽毛球", 1, "体育"),
    ("PE9004", "乒乓球", 1, "体育"),
    ("PE9005", "游泳", 1, "体育"),
]

# 任课教师池（按专业分组轮转分配）
TEACHERS = [
    "王建国", "李慧敏", "张伟", "刘洋", "陈静", "杨帆", "赵磊", "黄丽",
    "周强", "吴敏", "徐涛", "孙悦", "马超", "朱琳", "胡军", "郭婷",
    "何平", "高翔", "林雪", "罗刚", "郑华", "梁静", "谢峰", "唐宁",
]

DAYS = ["星期一", "星期二", "星期三", "星期四", "星期五"]
# 每个时段固定 2 小时：上午 / 下午 / 晚上
TIME_SLOTS = [
    ("上午", "08:30", "10:30"),
    ("下午", "14:00", "16:00"),
    ("晚上", "19:00", "21:00"),
]
ALL_SLOTS = [(day, period, start, end) for day in DAYS for period, start, end in TIME_SLOTS]


def build_course_meta():
    """为每门课分配任课教师和 2 小时上课时段。

    同一专业内的课程使用互不相同的时段，保证学生最多选 5 门时有足够选择；
    公共课/体育/英语也各自占用不同时段。
    """
    groups: dict[str, list[str]] = {}
    for code, _name, _credit, major in COURSES:
        groups.setdefault(major, []).append(code)

    meta = {}
    for group_index, (major, codes) in enumerate(groups.items()):
        offset = (group_index * 3) % len(ALL_SLOTS)
        for i, code in enumerate(codes):
            day, period, start, end = ALL_SLOTS[(offset + i) % len(ALL_SLOTS)]
            teacher = TEACHERS[(group_index * 3 + i) % len(TEACHERS)]
            meta[code] = (teacher, day, period, start, end, "第1-13周")
    return meta


def build_extra_meta():
    """为扩展课程分配教师和 2 小时时段。

    同一专业的新增课程使用互不相同的时段，保证每个专业至少能选出
    5 门时间不冲突的课程。
    """
    existing_counts: dict[str, int] = {}
    for _code, _name, _credit, major in COURSES:
        existing_counts[major] = existing_counts.get(major, 0) + 1

    groups: dict[str, list[str]] = {}
    for code, _name, _credit, major in EXTRA_COURSES:
        groups.setdefault(major, []).append(code)

    meta = {}
    for group_index, (major, codes) in enumerate(groups.items()):
        base = existing_counts.get(major, 0)
        for i, code in enumerate(codes):
            day, period, start, end = ALL_SLOTS[(group_index * 3 + base + i) % len(ALL_SLOTS)]
            teacher = TEACHERS[(group_index * 7 + base + i) % len(TEACHERS)]
            meta[code] = (teacher, day, period, start, end, "第1-13周")
    return meta


COURSE_META = {**build_course_meta(), **build_extra_meta()}


def ensure_columns():
    """旧数据库补齐新增列（简单迁移）。"""
    adds = {
        "courses": {
            "major": "VARCHAR DEFAULT ''",
            "teacher": "VARCHAR DEFAULT ''",
            "day": "VARCHAR DEFAULT ''",
            "period": "VARCHAR DEFAULT ''",
            "start_time": "VARCHAR DEFAULT ''",
            "end_time": "VARCHAR DEFAULT ''",
            "weeks": "VARCHAR DEFAULT ''",
        },
        "students": {
            "age": "INTEGER DEFAULT 0",
            "grade": "VARCHAR DEFAULT ''",
            "major_code": "VARCHAR DEFAULT ''",
            "gender": "VARCHAR DEFAULT ''",
            "id_card": "VARCHAR",
        },
        "users": {
            "role": "VARCHAR DEFAULT 'student'",
            "student_id": "INTEGER",
        },
    }
    insp = inspect(engine)
    for table, cols in adds.items():
        if table not in insp.get_table_names():
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        for col, ddl in cols.items():
            if col not in existing:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
                print(f"已为 {table} 表补充 {col} 列")


def seed_majors(db) -> None:
    """写入专业字典表（majors），保证 students.major_code 外键有对应记录。"""
    for name, code in MAJOR_CODES.items():
        if db.query(models.Major).filter_by(code=code).first() is None:
            db.add(models.Major(code=code, name=name))
    db.commit()


def seed():
    Base.metadata.create_all(bind=engine)
    ensure_columns()

    db = SessionLocal()
    try:
        seed_majors(db)
        for code, name, credit, major in COURSES + EXTRA_COURSES:
            teacher, day, period, start_time, end_time, weeks = COURSE_META[code]
            existing = db.query(models.Course).filter_by(course_code=code).first()
            if existing:
                existing.name = name
                existing.credit = credit
                existing.major = major
                existing.capacity = 50
                existing.teacher = teacher
                existing.day = day
                existing.period = period
                existing.start_time = start_time
                existing.end_time = end_time
                existing.weeks = weeks
            else:
                db.add(models.Course(
                    course_code=code, name=name, credit=credit, major=major,
                    capacity=50, teacher=teacher, day=day, period=period,
                    start_time=start_time, end_time=end_time, weeks=weeks,
                ))
        db.commit()
        total = db.query(models.Course).count()
        print(f"课程导入完成，共处理 {len(COURSES) + len(EXTRA_COURSES)} 门，当前课程总数 {total} 门")
    finally:
        db.close()


def create_default_user():
    db = SessionLocal()
    try:
        # 老师账号（最高权限）
        teacher = db.query(models.User).filter_by(username="teacher").first()
        if teacher is None:
            db.add(models.User(username="teacher", hashed_password=hash_password("teacher123"), role="teacher"))
            print("已创建老师账号：teacher / teacher123")
        else:
            teacher.role = "teacher"
        # 兼容：把旧的 admin 也设为老师角色
        admin = db.query(models.User).filter_by(username="admin").first()
        if admin is not None and admin.role != "teacher":
            admin.role = "teacher"
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    create_default_user()
