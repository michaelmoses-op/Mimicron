FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY cmd ./cmd
COPY internal ./internal
RUN CGO_ENABLED=0 go build -o /sim-engine ./cmd/sim-engine

FROM alpine:3.20
RUN apk add --no-cache wget
COPY --from=build /sim-engine /usr/local/bin/sim-engine
ENV HTTP_ADDR=:8090
EXPOSE 8090
CMD ["sim-engine"]
