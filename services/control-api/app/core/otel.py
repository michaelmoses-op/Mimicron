"""Optional OpenTelemetry export (OTLP). W3C tracecontext on HTTP."""

from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.context import attach, detach
from opentelemetry.propagate import extract, set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _OTEL_SDK = True
except ImportError:  # pragma: no cover - minimal dev installs
    _OTEL_SDK = False
    OTLPSpanExporter = None  # type: ignore[misc, assignment]
    FastAPIInstrumentor = None  # type: ignore[misc, assignment]
    Resource = None  # type: ignore[misc, assignment]
    TracerProvider = None  # type: ignore[misc, assignment]
    BatchSpanProcessor = None  # type: ignore[misc, assignment]
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_configured = False


def configure_otel(service_name: str) -> None:
    global _configured
    if _configured:
        return
    set_global_textmap(CompositePropagator([TraceContextTextMapPropagator()]))
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if endpoint and _OTEL_SDK:
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    _configured = True


def instrument_fastapi(app: object) -> None:
    if _OTEL_SDK and os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip():
        FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]


class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        token = attach(extract(request.headers))
        try:
            span_ctx = trace.get_current_span().get_span_context()
            if span_ctx.is_valid:
                request.state.trace_id = format(span_ctx.trace_id, "032x")
            else:
                request.state.trace_id = ""
            return await call_next(request)
        finally:
            detach(token)
