FROM node:22-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

FROM node:22-alpine
WORKDIR /app
RUN apk add --no-cache wget
COPY package.json ./
RUN npm install --omit=dev
COPY --from=build /app/dist ./dist
ENV PORT=8082
EXPOSE 8082
CMD ["node", "dist/index.js"]
