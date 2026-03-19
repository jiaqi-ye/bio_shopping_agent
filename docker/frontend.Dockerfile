FROM node:20-bullseye-slim

WORKDIR /app

ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE

# ✅ 只复制依赖文件
COPY frontend/package.json frontend/package-lock.json* ./

# ✅ 关键修复（避免 npm optional bug）
RUN npm cache clean --force
RUN rm -rf node_modules package-lock.json
RUN npm install --include=optional

# ✅ 再复制源码
COPY frontend/ ./

# ✅ build
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]