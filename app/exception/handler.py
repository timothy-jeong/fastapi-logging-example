from typing import List, LiteralString
import traceback
import json

from fastapi import Request, Response
from fastapi.exceptions import HTTPException

from app.exception import MyCustomException, ErrorCode

async def my_exception_handler(request: Request, exc: MyCustomException):
    await _pass_error_info(
        request=request,
        my_exception= exc,
        stack_trace=traceback.format_exc().splitlines())
    return await _to_response(my_exception=exc)

async def general_exception_handler(request: Request, exc: Exception):
    my_exception = MyCustomException(error_code=ErrorCode.UNEXPECTED)
    
    await _pass_error_info(
        request=request,
        my_exception= my_exception,
        stack_trace=traceback.format_exc().splitlines())
    return await _to_response(my_exception=my_exception)
    
async def http_exception_handler(request: Request, exc: HTTPException):
    my_exception = MyCustomException(http_exception=exc)
    await _pass_error_info(
        request=request,
        my_exception= my_exception,
        stack_trace=traceback.format_exc().splitlines())
    return await _to_response(my_exception=my_exception)    
    
async def _pass_error_info(
    request: Request,
    my_exception: MyCustomException,
    stack_trace: List[LiteralString]
    ):
        request.state.error_info = {
            "code": my_exception.code,
            "message": my_exception.reason,
            "http_status": my_exception.http_status,
            "stack_trace": stack_trace,
    }

async def _to_response(my_exception: MyCustomException):
        return Response(
            status_code=my_exception.http_status,
            content=json.dumps(
                {"code":my_exception.code, "message":my_exception.reason}, ensure_ascii=False).encode('utf-8')
            )
    