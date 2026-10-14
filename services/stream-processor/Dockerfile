# 1.81 is too old for current crates.io (e.g. idna_adapter needs edition 2024 / Cargo 1.85+).
FROM rust:1.85-bookworm AS build
RUN apt-get update && apt-get install -y --no-install-recommends cmake libssl-dev pkg-config \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates libssl3 \
  && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/release/stream-processor /usr/local/bin/stream-processor
ENV HTTP_ADDR=0.0.0.0:8091
EXPOSE 8091
CMD ["stream-processor"]
