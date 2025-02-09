# FastAPI JSON Logging Example

This repository demonstrates how to implement structured JSON logging in a FastAPI application, capturing access, exception, performance, and security-related information.  Instead of relying on uvicorn's access logs, this approach provides a more comprehensive and easily parsable log format.

## Key Features

* **JSON Logging:** All logs are formatted as JSON, making them easy to parse and analyze with log management tools.
* **Comprehensive Logging:**  Includes access logs (request details), exception logs (error details and stack traces), performance logs (request time, database query time), and security logs (specific error types).
* **Customizable:** Easily configure which information is included in the logs.
* **Uvicorn Log Suppression:**  Disables uvicorn's default access logs to avoid duplication and ensure only the structured JSON logs are used.
* **Error Handling:**  Includes custom exception handling and logging of both expected and unexpected errors.
* **Database Query Time Tracking:** Tracks the time spent on database queries for performance analysis, in this example just **cursor time**

## Project Structure

```bash
├── app
│   ├── database.py       # Database connection and query time tracking
│   ├── exception
│   │   ├── handler.py    # Exception handling and JSON error response
│   │   └── init.py
│   ├── logger
│   │   ├── logger_setup.py # Logger setup and configuration
│   │   └── init.py
│   ├── middleware
│   │   ├── json_logger.py # JSON logging middleware
│   │   └── init.py
│   ├── util
│   │   ├── env.py # utils for environment variable
│   │   └── init.py
│   ├── init.py
│   └── main.py            # Main application file
```

## Code Highlights

### `app/middleware/json_logger.py`

This middleware intercepts every request and generates a JSON log entry.  It captures:

* **Access Information:** Timestamp, event ID, method, path, client IP, user agent.
* **Performance Information:** Request processing time (`time_taken_ms`), database query time (`db_query_time_ms`).
* **Exception Information:**  Error code, error message, exception type, stack trace.
* **Security Information:**  Logs specific error types as security-related.
* **Log Type and Level:** `log_type` (access, error, security), `level` (INFO, ERROR).
* **Status Code:** HTTP status code of the response.

It also handles exceptions and extracts error information from custom exceptions (`MyCustomException`) passed by the exception handler.

### `app/logger/logger_setup.py`

This module sets up the `request-logger` to output JSON strings.  It's crucial for ensuring the logs are properly formatted.  It also disables uvicorn's access logs to prevent redundant logging.

### `app/exception/handler.py`

This module defines exception handlers for `MyCustomException` and general exceptions.  It formats error responses as JSON and, importantly, passes error information (code, message, HTTP status, stack trace) to the middleware via `request.state.error_info` for inclusion in the log.

### `app/database.py`

This module handles database interactions and includes a mechanism for tracking database query execution time. The query time is then made available to the middleware via `request.state`.

## Usage

1.  **Installation:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Running the application:**

    ```bash
    uvicorn main:app --reload
    ```

3.  **Environment Variables:**

    *   `IS_JSON_LOGGING`: Enables/disables JSON logging (default: `True`).
    *   `IS_STACKTRACE_LOGGING`: Enables/disables stack trace logging (default: `True`).

## Example Log Output

```json
{"timestamp": "2024-10-27T12:34:56.789Z", "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "method": "GET", "path": "/items/some-uuid", "client_ip": "127.0.0.1", "user_agent": "...", "time_taken_ms": 123, "log_type": "error", "level": "ERROR", "status_code": 404, "error_code": "ENTITY_NOT_FOUND", "error_message": "item을 찾을 수 없습니다", "stack_trace": ["Traceback (most recent call last): ..."],
