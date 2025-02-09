import logging
import traceback
import time
import uuid
import json

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.logger.logger_setup import REQUEST_LOGGER_NAME
from app.exception import ErrorCode, MyCustomException
from app.util.env import get_bool_from_env

logger = logging.getLogger(REQUEST_LOGGER_NAME)

STACKTRACE_LOGGING_ENABLED = get_bool_from_env("IS_STACKTRACE_LOGGING", True)


class JsonRequestLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        event_id = str(uuid.uuid4())

        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "event_id": event_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent"),
        }

        try:
            response = await call_next(request)
            status_code = response.status_code
            log_type = "access"

        except Exception as e: 
            status_code = 500 
            log_type = "error"
            log_data['error_code'] = "UNEXPECTED_ERROR" # Or some default code
            log_data['exception'] = type(e).__name__
            log_data['error_message'] = str(e) # Log the exception message as fallback
            log_data['stack_trace'] = traceback.format_exc().splitlines()

            application_exception = MyCustomException(ErrorCode.UNEXPECTED)
            response = application_exception.to_error_response()


        error_info = getattr(request.state, "error_info", None)  # Use getattr

        if error_info:  # exception handler 에서 넘기는 error_info 정보 확인

            status_code = error_info.get("http_status", getattr(ErrorCode.UNEXPECTED, "http_status", 500)) # Use status code from error_info, Default 500
            log_type = "error" if status_code >= 400 and status_code not in [401, 403] else 'security'

            log_data.update({  # error_info 를 log data 에 추가
                "error_code": error_info.get("code"),
                "error_message": error_info.get("message"),
                "stack_trace": error_info.get("stack_trace") if (STACKTRACE_LOGGING_ENABLED or error_info.get("code") == ErrorCode.UNEXPECTED.code) else None,
            })


        log_level = "ERROR" if status_code >= 400 else "INFO"

        log_data['time_taken_ms'] = int((time.time() - start_time) * 1000)
        log_data['log_type'] = log_type
        log_data['level'] = log_level
        log_data['status_code'] = status_code
        log_data['db_query_time_ms'] = getattr(request.state, "db_query_time_ms", None)

        # https://docs.python.org/3/library/logging.html#logging.getLevelName 의 Changed in version 3.4 에 따르면
        # logging.getLevelName(str) 은 유지되긴 하지만 실수였다고 한다. 이를 최대한 사용하지 않기 위해 이런 방법을 이용헀다.
        log_level_int: int = logging.getLevelNamesMapping()[log_level] 
        logger.log(log_level_int,json.dumps(log_data, ensure_ascii=False).encode('utf-8'))

        return response