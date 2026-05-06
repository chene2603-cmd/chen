from fastapi import FastAPI
from src.api.routes import router
from src.utils.logging_config import setup_logging

# 启动时初始化日志
setup_logging(log_level='INFO', log_file='logs/oracle.log')

app = FastAPI(
    title="OpenOracle API",
    description="公开AI预测系统",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "OpenOracle"}