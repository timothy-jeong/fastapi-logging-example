# JsonRequestLogger Middleware

The JsonRequestLoggerMiddleware logs incoming HTTP requests in JSON format. It captures useful metadata such as timestamp, event ID, HTTP method, path, client IP (using configurable header names), user agent, processing time, and error information (if available). This middleware is designed to be integrated into a FastAPI application.

> Note: <br/>
Due to FastAPI/Starlette’s internal exception handling, when a 500 error occurs the error information may not be captured by the logger because the built-in ExceptionMiddleware intercepts exceptions before your middleware is invoked. In such cases, it’s recommended to log error details directly within your exception handlers.

## Features
- JSON Logging: Logs request details in a structured JSON format.
- Configurable Options:
    - Event ID: Optionally extract an event ID from a specified header; if absent, a new UUID is generated.
    - Client IP: Extract client IP from headers like X-Forwarded-For or X-Real-IP (configurable).
    - Error Info Mapping: Define which keys from the error info (set by exception handlers) should be logged.
    - Custom Logger: Optionally supply your own logging.Logger instance.

## Installation
Install the required packages (e.g., FastAPI, uvicorn) as specified in your project's `requirements.txt`:

```bash
pip install -r requirements.txt
```

Place the `JsonRequestLoggerMiddleware` in your project (for example, under `app/middleware/json_logger.py`).

## Usage
Basic Integration
You can add the middleware to your FastAPI app using `app.add_middleware()`:

```python
from fastapi import FastAPI
from app.middleware.json_logger import JsonRequestLoggerMiddleware

app = FastAPI()

# Add JSON Request Logger Middleware with custom configuration.
app.add_middleware(
    JsonRequestLoggerMiddleware,
    event_id_header="X-Event-ID",              # Use this header for event ID; if absent, a new UUID is generated.
    client_ip_headers=["x-forwarded-for", "x-real-ip"],  # List of headers to determine the client IP.
    error_info_mapping={
        "code": "error_code",
        "message": "error_message",
        "stack_trace": "stack_trace"
    }
)
```

## Middleware Configuration Options
When initializing the middleware, you can set the following options:

- error_info_name (str):
The key in the request state where error information is stored (default: "error_info").

- error_info_mapping (dict[str, str] | None):
A mapping that specifies which keys from the error info should be logged.
For example, { "code": "error_code", "message": "error_message", "stack_trace": "stack_trace" }.

- event_id_header (str | None):
The HTTP header name used to extract the event ID. If not provided or if the header is missing, a new UUID is generated.

- client_ip_headers (list[str] | None):
A list of HTTP header names that should be checked (in order) for the client’s IP address.
If none of these headers are found, the client IP is taken from scope["client"].

- logger (logging.Logger | None):
A custom logger instance. If not provided, a default logger is created with INFO level logging.


## Example JSON Log Output
A typical log entry might look like this:

```json
{
  "timestamp": "2025-03-02T08:17:40.123456Z",
  "event_id": "ab427b0c-629b-4792-891e-bce4c94d1084",
  "method": "GET",
  "path": "/items/3fa85f64-5717-4562-b3fc-2c963f66afa4",
  "client_ip": "203.0.113.195",
  "user_agent": "Mozilla/5.0 (Macintosh; ...)",
  "time_taken_ms": 12,
  "status_code": 200,
  "log_type": "access",
  "level": "INFO"
}
```

If error information is present (set by your exception handlers), the log entry will also include keys like `"error_code"`, `"error_message"`, and `"stack_trace"`.

## Known Limitations
### 500 Errors:
When a 500 error occurs, FastAPI’s built-in ExceptionMiddleware intercepts the error and may not propagate the error info to your middleware as expected. For detailed error logging in such cases, log error details directly within your exception handlers.

---
This README should help users integrate and configure the JsonRequestLogger in their FastAPI project.