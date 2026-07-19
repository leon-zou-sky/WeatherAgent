FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码和模型
COPY . .
COPY models/ /app/models/

# 暴露端口：8000=FastAPI, 9000=MCP SSE
EXPOSE 8000 9000

# 启动命令
CMD ["python", "start_services.py"]
