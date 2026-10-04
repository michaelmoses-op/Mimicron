FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY cmd ./cmd
RUN go build -o /ingestion-gateway ./cmd/ingestion-gateway

FROM alpine:3.20
RUN apk add --no-cache wget
COPY --from=build /ingestion-gateway /usr/local/bin/ingestion-gateway
ENV HTTP_ADDR=:8081
EXPOSE 8081
CMD ["ingestion-gateway"]
