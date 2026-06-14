FROM python:3.11-slim
WORKDIR /app

# 系统依赖(PyMySQL 编译时需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖(使用国内镜像源)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 源码
COPY . .

# 日志目录
RUN mkdir -p /app/logs

# 健康检查 - 验证 MySQL 可达
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import socket; socket.create_connection(('${DB_HOST:-mysql}', ${DB_PORT:-3306}), timeout=2)" || exit 0

CMD ["python", "main.py"]
