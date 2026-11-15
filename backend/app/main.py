from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import Base, engine
from .routers import auth, courses, enrollments, students

Base.metadata.create_all(bind=engine)


class UTF8JSONResponse(JSONResponse):
    """显式声明 charset，避免浏览器用本地编码解析 UTF-8 中文 JSON。"""

    media_type = "application/json; charset=utf-8"


app = FastAPI(
    title="学生选课系统 API",
    description="学生选课系统的后端接口文档，提供学生、课程的管理，以及选课/退课功能。",
    version="0.2.0",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(enrollments.router)


@app.get("/")
def root():
    return {"message": "学生选课系统 API 已启动"}
