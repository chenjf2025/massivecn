# 国内股票行情网关 - 后端 Dockerfile
# 支持多架构构建 (linux/amd64, linux/arm64)

FROM python:3.10-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY backend/requirements.txt .

# 安装 Python 依赖 (使用默认 PyPI)
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/*.py .
COPY backend/parsers ./parsers

# 创建默认配置文件
RUN echo 'sources:' > config.yaml && \
    echo '  primary:' >> config.yaml && \
    echo '    - name: eastmoney' >> config.yaml && \
    echo '      enabled: true' >> config.yaml && \
    echo '      priority: 1' >> config.yaml && \
    echo '    - name: xueqiu' >> config.yaml && \
    echo '      enabled: false' >> config.yaml && \
    echo '      priority: 2' >> config.yaml && \
    echo '  backup:' >> config.yaml && \
    echo '    - name: tencent' >> config.yaml && \
    echo '      enabled: true' >> config.yaml && \
    echo '      priority: 1' >> config.yaml && \
    echo '    - name: sina' >> config.yaml && \
    echo '      enabled: false' >> config.yaml && \
    echo '      priority: 2' >> config.yaml
RUN echo 'sources:' > config.yaml && \
    echo '  primary:' >> config.yaml && \
    echo '    - name: eastmoney' >> config.yaml && \
    echo '      enabled: true' >> config.yaml && \
    echo '  backup:' >> config.yaml && \
    echo '    - name: tencent' >> config.yaml && \
    echo '      enabled: true' >> config.yaml
# 复制配置文件
COPY config.yaml .

# 暴露端口
# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
