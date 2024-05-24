INFO:     Started server process [7]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8040 (Press CTRL+C to quit)
INFO:     172.17.0.1:36390 - "POST /send_email HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/usr/local/lib/python3.9/site-packages/aiosmtplib/smtp.py", line 479, in _create_connection
    transport, _ = await asyncio.wait_for(connect_coro, timeout=timeout)
  File "/usr/local/lib/python3.9/asyncio/tasks.py", line 479, in wait_for
    return fut.result()
  File "uvloop/loop.pyx", line 2039, in create_connection
  File "uvloop/loop.pyx", line 2016, in uvloop.loop.Loop.create_connection
ConnectionRefusedError: [Errno 111] Connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/usr/local/lib/python3.9/site-packages/uvicorn/protocols/http/httptools_impl.py", line 411, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
  File "/usr/local/lib/python3.9/site-packages/uvicorn/middleware/proxy_headers.py", line 69, in __call__
    return await self.app(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/applications.py", line 123, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/usr/local/lib/python3.9/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/usr/local/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 65, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 756, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 776, in app
    await route.handle(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 297, in handle
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 77, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 72, in app
    response = await func(request)
  File "/usr/local/lib/python3.9/site-packages/fastapi/routing.py", line 278, in app
    raw_response = await run_endpoint_function(
  File "/usr/local/lib/python3.9/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
  File "/app/routes/send_email.py", line 18, in send_email_endpoint
    await send_email(to_address, subject, body, file_url)
  File "/app/dependencies.py", line 112, in send_email
    await aiosmtplib.send(
  File "/usr/local/lib/python3.9/site-packages/aiosmtplib/api.py", line 121, in send
    async with client:
  File "/usr/local/lib/python3.9/site-packages/aiosmtplib/smtp.py", line 172, in __aenter__
    await self.connect()
  File "/usr/local/lib/python3.9/site-packages/aiosmtplib/smtp.py", line 430, in connect
    raise exc
  File "/usr/local/lib/python3.9/site-packages/aiosmtplib/smtp.py", line 425, in connect
    response = await self._create_connection(
  File "/usr/local/lib/python3.9/site-packages/aiosmtplib/smtp.py", line 485, in _create_connection
    raise SMTPConnectError(
aiosmtplib.errors.SMTPConnectError: Error connecting to mail.vontainment.com on port 587: [Errno 111] Connection refused
INFO:     172.17.0.1:50312 - "POST /send_email HTTP/1.1" 200 OK
INFO:     172.17.0.1:36554 - "POST /send_email HTTP/1.1" 200 OK
INFO:     172.17.0.1:38728 - "POST /send_email HTTP/1.1" 422 Unprocessable Entity
INFO:     172.17.0.1:33432 - "POST /send_email HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/usr/local/lib/python3.9/site-packages/uvicorn/protocols/http/httptools_impl.py", line 411, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
  File "/usr/local/lib/python3.9/site-packages/uvicorn/middleware/proxy_headers.py", line 69, in __call__
    return await self.app(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/applications.py", line 123, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/usr/local/lib/python3.9/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/usr/local/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 65, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 756, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 776, in app
    await route.handle(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 297, in handle
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 77, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 72, in app
    response = await func(request)
  File "/usr/local/lib/python3.9/site-packages/fastapi/routing.py", line 278, in app
    raw_response = await run_endpoint_function(
  File "/usr/local/lib/python3.9/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
  File "/app/routes/send_email.py", line 18, in send_email_endpoint
    await send_email(to_address, subject, body, file_url)
  File "/app/dependencies.py", line 88, in send_email
    for url in file_url:
TypeError: 'pydantic_core._pydantic_core.Url' object is not iterable
INFO:     172.17.0.1:42230 - "POST /send_email HTTP/1.1" 403 Forbidden
from fastapi import APIRouter, Depends, HTTPException
from models import SendEmailRequest
from dependencies import send_email, get_api_key

send_router = APIRouter()


@send_router.post("/send_email", operation_id="send_an_email")
async def send_email_endpoint(
    request: SendEmailRequest, api_key: str = Depends(get_api_key)
):
    to_address = request.to_address
    subject = request.subject
    body = request.body
    file_url = request.file_url

    try:
        await send_email(to_address, subject, body, file_url)
        return {"message": "Email sent successfully"}
    except HTTPException as e:
        return {"message": f"Failed to send email: {e.detail}"}
