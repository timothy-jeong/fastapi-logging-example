import logging

REQUEST_LOGGER_NAME = "request-logger"


def setup_request_logger() -> logging.Logger:
    """
    request-logger를 순수 JSON 문자열로 찍는 로거를 설정하고 반환한다.
    """
    logger = logging.getLogger(REQUEST_LOGGER_NAME)
    logger.setLevel(logging.INFO)

    # 혹시 이미 다른 곳에서 핸들러가 붙었다면 제거
    if logger.hasHandlers():
        logger.handlers.clear()

    # 스트림 핸들러 생성
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    # 포매터 설정
    formatter = logging.Formatter("%(message)s")  
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    # propagate=False 로 설정하면 root logger로 로그가 전파되지 않음, 라이브러간 영향 없애기
    logger.propagate = False

    return logger

def disable_uvicorn_logs():
    """
    uvicorn.access 로거에 대해 disabled=True 설정
    """
    for name in logging.root.manager.loggerDict:
        if "uvicorn.access" in name:
            logging.getLogger(name).disabled = True