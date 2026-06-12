# ============================================================
#  Dockerfile - 临床研发流程自动化助手
#  多阶段构建，优化镜像大小
# ============================================================

# ---------- 第一阶段：依赖安装 ----------
FROM python:3.11-slim AS builder

LABEL maintainer="Clinical R&D Process Automation Assistant"
LABEL description="临床研发流程自动化助手 - Clinical R&D Process Automation Assistant"
LABEL version="1.0.0"

# 设置工作目录
WORKDIR /app

# 安装系统依赖（语音处理所需）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt


# ---------- 第二阶段：运行镜像 ----------
FROM python:3.11-slim

WORKDIR /app

# 从 builder 阶段复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p data/uploads data/samples data/task_storage logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV APP_DEBUG=false
ENV LLM_PROVIDER=mock

# 暴露端口
EXPOSE 8501 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501')" || exit 1

# 默认启动命令（可通过 docker-compose 覆盖）
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
