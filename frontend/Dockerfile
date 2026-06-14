# ---------- 阶段 1: 构建 ----------
FROM node:20-alpine AS builder
WORKDIR /app

# 国内构建加速
RUN npm config set registry https://registry.npmmirror.com

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---------- 阶段 2: Nginx 托管 ----------
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
