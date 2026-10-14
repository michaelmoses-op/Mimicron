FROM node:22-alpine AS build
WORKDIR /app
ARG VITE_API_URL=http://localhost:8000
ARG VITE_STREAM_URL=http://localhost:8082
ENV VITE_API_URL=$VITE_API_URL VITE_STREAM_URL=$VITE_STREAM_URL
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
