from collections.abc import Mapping
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException


class ValidationIssue(BaseModel):
    location: list[str | int]
    message: str


class ProblemDetails(BaseModel):
    type: Literal["about:blank"] = "about:blank"
    title: str
    status: int
    detail: str
    request_id: str
    errors: list[ValidationIssue] | None = None


def problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    errors: list[ValidationIssue] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    problem = ProblemDetails(
        title=title,
        status=status,
        detail=detail,
        request_id=getattr(request.state, "request_id", "unavailable"),
        errors=errors,
    )
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return problem_response(
            request,
            status=exc.status_code,
            title="Request failed",
            detail=str(exc.detail),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return problem_response(
            request,
            status=422,
            title="Validation failed",
            detail="One or more request fields are invalid.",
            errors=[
                ValidationIssue(location=list(error["loc"]), message="Invalid value")
                for error in exc.errors()
            ],
        )

    original_openapi = app.openapi

    def problem_openapi() -> dict[str, object]:
        # FastAPI registers model-backed errors as application/json by default.
        # Keep the generated client aligned with the actual problem-details media type.
        schema = original_openapi()
        for path in schema["paths"].values():
            for method, operation in path.items():
                if method not in {
                    "get",
                    "put",
                    "post",
                    "delete",
                    "patch",
                    "options",
                    "head",
                    "trace",
                }:
                    continue
                for status, response in operation.get("responses", {}).items():
                    if status != "default" and not (status.isdecimal() and int(status) >= 400):
                        continue
                    content = response.get("content", {})
                    reference = content.get("application/json", {}).get("schema", {}).get("$ref")
                    if reference == "#/components/schemas/ProblemDetails":
                        content["application/problem+json"] = content.pop("application/json")
        return schema

    app.openapi = problem_openapi
