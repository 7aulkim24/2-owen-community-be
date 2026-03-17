import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from utils.errors.exceptions import APIError
from utils.common.response import StandardResponse
from utils.errors.error_codes import ErrorCode


logger = logging.getLogger(__name__)


def _map_http_status_to_error_code(status_code: int) -> ErrorCode:
    mapping = {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        409: ErrorCode.CONFLICT,
        413: ErrorCode.PAYLOAD_TOO_LARGE,
        422: ErrorCode.INVALID_INPUT,
        429: ErrorCode.TOO_MANY_REQUEST,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
    }
    return mapping.get(status_code, ErrorCode.INTERNAL_SERVER_ERROR)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error: %s | Body: %s", exc.errors(), getattr(request, "_json", "N/A"))
    return JSONResponse(
        status_code=422,
        content=StandardResponse.validation_error(exc.errors()),
    )


async def api_exception_handler(request: Request, exc: APIError):
    logger.info("API error: %s | Status: %s | Message: %s", exc.code.name, exc.status_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=StandardResponse.error(exc.code, exc.details, exc.message),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    error_code = _map_http_status_to_error_code(exc.status_code)
    details = {"detail": exc.detail} if exc.detail else {}
    logger.warning("HTTP exception: %s | Status: %s | Detail: %s", error_code.name, exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=StandardResponse.error(error_code, details),
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unexpected error: %s | Path: %s | Method: %s", str(exc), request.url.path, request.method, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=StandardResponse.error(ErrorCode.INTERNAL_SERVER_ERROR, {}),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(APIError, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
