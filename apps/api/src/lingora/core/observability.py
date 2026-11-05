import json
import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from lingora.core.config import Settings
from lingora.core.errors import problem_response

logger = logging.getLogger("lingora.http")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "level": record.levelname,
                "event": record.getMessage(),
                "request_id": getattr(record, "request_id", None),
                "method": getattr(record, "method", None),
                "route": getattr(record, "route", None),
                "status": getattr(record, "status", None),
                "duration_ms": getattr(record, "duration_ms", None),
            }
        )


def configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False


def create_tracer_provider(settings: Settings) -> TracerProvider:
    provider = TracerProvider(resource=Resource.create({"service.name": "lingora-api"}))
    if settings.otel_exporter_otlp_endpoint:
        endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/") + "/v1/traces"
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    return provider


def register_request_middleware(app: FastAPI, provider: TracerProvider) -> None:
    tracer = provider.get_tracer("lingora.http")

    @app.middleware("http")
    async def observe_request(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        started = time.monotonic()
        # Record route templates only, never URLs, query strings, headers, or bodies.
        with tracer.start_as_current_span("http.request", kind=trace.SpanKind.SERVER) as span:
            try:
                response = await call_next(request)
            except Exception:
                response = problem_response(
                    request,
                    status=500,
                    title="Internal server error",
                    detail="An unexpected error occurred.",
                )
            route = getattr(request.scope.get("route"), "path", "[unmatched]")
            span.update_name(f"{request.method} {route}")
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("http.route", route)
            span.set_attribute("http.response.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "http.request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "route": route,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                },
            )
            return response
