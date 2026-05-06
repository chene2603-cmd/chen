# OpenOracle 主服务镜像
FROM python:3.11-slim

LABEL maintainer="OpenOracle Team"
LABEL description="OpenOracle - 公开AI预测系统"
LABEL version="1.0.0"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OPENORACLE_HOME=/app

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/logs /app/data /app/config

# 创建非 root 用户
RUN useradd -m -u 1000 -s /bin/bash oracle && \
    chown -R oracle:oracle /app
USER oracle

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]