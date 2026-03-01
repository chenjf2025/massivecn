# 前端 Dockerfile
# 构建 Vue 3 应用并使用 Nginx 托管

# 构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY frontend/package.json ./

# 安装依赖 (使用国内镜像)
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

# 复制源代码
COPY frontend/ ./

# 构建
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
