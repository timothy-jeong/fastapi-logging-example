from enum import Enum
from typing import Optional, Dict

from fastapi import status


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
            error_code: ErrorCode,
            reason: Optional[str] = None,
    ):
        self.http_status = error_code.http_status
        self.code = error_code.code
        self.reason = reason if reason else error_code.reason
        super().__init__(self.reason)

    def to_error_response(self) -> Dict:
        return {"code": self.code, "message": self.reason}