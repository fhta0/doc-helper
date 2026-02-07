# 构建阶段
FROM node:22.17.1-bullseye-slim as build-stage

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# 生产阶段 - Nginx 将在 docker-compose 中单独配置，这里仅作为构建产物提供者
# 或者如果想做成独立容器，可以使用 nginx:alpine
FROM nginx:alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
