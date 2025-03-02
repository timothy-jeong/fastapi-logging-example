from enum import Enum
from typing import Dict

from fastapi import status
from fastapi.exceptions import HTTPException


class ErrorCode(Enum):
    ENTITY_NOT_FOUND = (status.HTTP_404_NOT_FOUND, "This", "대상을 찾을 수 없습니다.")
    ENTITY_ALREADY_EXISTS = (status.HTTP_409_CONFLICT, "Is", "DB 엔티티가 중복되었습니다.")
    UNEXPECTED = (status.HTTP_500_INTERNAL_SERVER_ERROR, "Example", "예상치 못한 오류가 발생하였습니다.")

    def __init__(self, http_status, code, reason):
        self.http_status = http_status
        self.code = code
        self.reason = reason


class MyCustomException(Exception):
    def __init__(
            self,
            error_code: ErrorCode | None = None,
            http_exception: HTTPException | None = None,
            reason: str | None = None
    ):
        if http_exception:
            self.http_status = http_exception.status_code
            self.code = "HTTP"
            self.reason = reason if reason else http_exception.detail    
            super().__init__(http_exception.detail)
        else:            
            self.http_status = error_code.http_status
            self.code = error_code.code
            self.reason = reason if reason else error_code.reason
            super().__init__(self.reason)

    def to_error_response(self) -> Dict:
        return {"code": self.code, "message": self.reason}