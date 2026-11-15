from pydantic import BaseModel, ConfigDict


class StudentBase(BaseModel):
    student_no: str
    name: str
    major: str = ""
    email: str = ""
    age: int = 0
    grade: str = ""
    major_code: str = ""
    gender: str = ""
    id_card: str = ""


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StudentPage(BaseModel):
    total: int
    items: list[StudentRead]


class BatchDeleteRequest(BaseModel):
    ids: list[int]


class CourseBase(BaseModel):
    course_code: str
    name: str
    credit: int = 3
    capacity: int = 50
    teacher: str = ""
    major: str = ""
    day: str = ""
    period: str = ""
    start_time: str = ""
    end_time: str = ""
    weeks: str = ""


class CourseCreate(CourseBase):
    pass


class CourseRead(CourseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    enrolled_count: int = 0


class EnrollRequest(BaseModel):
    course_id: int


class LoginRequest(BaseModel):
    account: str  # 可以是用户名、学号或邮箱
    password: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str = "student"
    student_id: int | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    student_id: int | None = None
    major: str | None = None
    name: str | None = None


class StudentRegisterItem(BaseModel):
    name: str
    grade: str
    major: str = ""
    age: int = 0
    gender: str = ""
    id_card: str = ""


class BatchRegisterRequest(BaseModel):
    students: list[StudentRegisterItem]


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    new_password: str
