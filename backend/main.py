from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# 初始化数据库
from models.database import init_db
init_db()

from routers import analyze, cases, knowledge, stats

app = FastAPI(title="智调民和 API", version="0.1.0")

from routers import documents
app.include_router(documents.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analyze.router)
app.include_router(cases.router)
app.include_router(knowledge.router)
app.include_router(stats.router)

@app.get("/")
def root():
    return {"message": "智调民和 API 运行中", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
