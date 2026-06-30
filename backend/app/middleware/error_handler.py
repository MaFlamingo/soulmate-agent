"""Global exception handler for FastAPI."""

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler for unhandled errors."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if request.app.debug else None,
        },
    )
