# 1. 使用官方 Python 轻量级镜像作为基础
# slim 版本体积小，适合生产环境
FROM python:3.9-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 将依赖文件复制到容器中
COPY requirements.txt .

# 4. 安装依赖
# --no-cache-dir 可以减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 5. 将当前目录下的所有代码复制到容器的工作目录
COPY . .

# 6. 暴露 Streamlit 默认端口
EXPOSE 8501

# 7. 设置启动命令
# address=0.0.0.0 是必须的，否则在容器外无法访问
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]