from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

class AutomedgeException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class LeadNotFoundException(AutomedgeException):
    def __init__(self, lead_id: str):
        super().__init__(status_code=404, detail=f"Lead {lead_id} not found")

class UnauthorizedException(AutomedgeException):
    def __init__(self):
        super().__init__(status_code=401, detail="Invalid or missing token")

class WorkflowException(AutomedgeException):
    def __init__(self, message: str):
        super().__init__(status_code=500, detail=f"Workflow error: {message}")

async def automedge_exception_handler(request: Request, exc: AutomedgeException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.status_code},
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "An internal server error occurred", "code": 500},
    )
