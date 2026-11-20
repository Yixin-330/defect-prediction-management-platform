# 1. 使用轻量级的 Python 3.12 镜像
FROM python:3.12-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 【关键坑】安装 Git，否则 GitPython 无法工作
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 4. 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制项目所有代码
COPY . .

# 6. 暴露端口
EXPOSE 8000

# 7. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]