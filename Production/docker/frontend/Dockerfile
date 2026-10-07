FROM node:latest AS build

WORKDIR /app

COPY frontend/echo-smyta/package*.json ./

RUN npm install --force

COPY frontend/echo-smyta/ ./

RUN npm run build

FROM nginx:latest

RUN mkdir -p /etc/nginx/snippets

COPY docker/frontend/snippets/proxy_params.conf /etc/nginx/snippets/proxy_params.conf
COPY docker/frontend/snippets/cors_options.conf /etc/nginx/snippets/cors_options.conf

RUN rm /etc/nginx/conf.d/default.conf

COPY docker/frontend/nginx.conf /etc/nginx/nginx.conf

COPY --from=build /app/dist/ /usr/share/nginx/html/
