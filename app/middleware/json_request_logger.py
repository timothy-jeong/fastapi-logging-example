import logging
import time
import uuid
import json

from starlette.types import ASGIApp, Message, Scope, Receive, Send

class JsonRequestLoggerMiddleware:
    def __init__(
        self, app: ASGIApp,
        error_info_name: str = "error_info",
        error_info_mapping: dict[str, str] | None = None,
        event_id_header: str | None = None,
        client_ip_headers: list[str] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initializes the JSON Request Logger Middleware.

        Args:
            app (ASGIApp): The ASGI application instance to wrap.
            error_info_name (str, optional): The key name in the request state from which to extract error information.
                Defaults to "error_info".
            error_info_mapping (dict[str, str] | None, optional): A dictionary mapping error information keys (from the request
                state) to desired log field names. For example, {"code": "error_code", "message": "error_message"}.
                Defaults to None.
            event_id_header (str | None, optional): The HTTP header name to extract an event ID from. If not provided or if the header
                is missing, a new UUID will be generated. Defaults to None.
            client_ip_headers (list[str] | None, optional): A list of HTTP header names to check for the client IP address,
                in order of priority. If none are provided, the client IP will be obtained from the scope's "client" value.
                Defaults to None.
            logger (logging.Logger | None, optional): A custom logger to use for logging requests. If not provided, a default
                logger with INFO level is created. Defaults to None.
        """
        self.app = app
        self.error_info_name = error_info_name
        self.error_info_mapping = error_info_mapping or {
            "code": "error_code",
            "message": "error_message",
            "stack_trace": "stack_trace",
        }
        self.event_id_header = event_id_header
        self.client_ip_headers = client_ip_headers or ["x-forwarded-for", "x-real-ip"]
        # logger setting
        if logger:
            self.logger = logger
        else:
            logger = logging.getLogger("request-logger")
            logger.setLevel(logging.INFO)
            if logger.hasHandlers():
                logger.handlers.clear()
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(message)s")  
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            logger.propagate = False
            self.logger = logger
            
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()
        
        # parse header
        headers = {k.decode("latin1"): v.decode("latin1") for k, v in scope.get("headers", [])}
        # event_id
        if self.event_id_header and self.event_id_header in headers:
            event_id = headers[self.event_id_header]
        else:
            event_id = str(uuid.uuid4())
            
        # extract client ip from client_ip_headers
        client_ip = None
        for header in self.client_ip_headers:
            if header in headers:
                # X-Forwarded-For case
                client_ip = headers[header].split(",")[0].strip()
                break
        if not client_ip:
            client_ip = scope.get("client", ("unknown",))[0]
                        
        # default log data
        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "event_id": event_id,
            "method": scope.get("method"),
            "path": scope.get("path"),
            "client_ip": client_ip,
            "user_agent": headers.get("user-agent"),
        }

        response_status_code = None

        async def send_wrapper(message: Message) -> None:
            nonlocal response_status_code
            if message["type"] == "http.response.start":
                response_status_code = message.get("status")
            await send(message)

        await self.app(scope, receive, send_wrapper)
        
        time_taken_ms = int((time.time() - start_time) * 1000)
        
        # based on response status_code
        if response_status_code is None:
            response_status_code = 500
        log_type = "access" if response_status_code < 400 else "error"
        log_level = "ERROR" if response_status_code >= 400 else "INFO"
                
        # error log data
        
        error_info = scope.get("state", {}).get(self.error_info_name, None)
        if not error_info:
            log_data.update({"error": None})
        if error_info:
            log_data.update({"error": {}})
            for src_key, dest_key in self.error_info_mapping.items():
                log_data["error"][dest_key] = error_info.get(src_key)            
        
        # log data update
        log_data.update({
            "time_taken_ms": time_taken_ms,
            "status_code": response_status_code,
            "log_type": log_type,
            "level": log_level,
        })     
        
        log_level_int = logging.getLevelNamesMapping()[log_level]
        self.logger.log(log_level_int, json.dumps(log_data, ensure_ascii=False))