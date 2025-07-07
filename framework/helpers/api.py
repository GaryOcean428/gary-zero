import json
import threading
import time
from abc import abstractmethod
from typing import Any, TypedDict, Union

from flask import Flask, Request, Response

from agent import AgentContext
from initialize import initialize_agent
from framework.helpers.errors import format_error
from framework.helpers.print_style import PrintStyle

Input = dict
Output = Union[dict[str, Any], Response, TypedDict]  # type: ignore


class ApiHandler:
    def __init__(self, app: Flask, thread_lock: threading.Lock):
        self.app = app
        self.thread_lock = thread_lock

    @classmethod
    def requires_loopback(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @abstractmethod
    async def process(self, input_data: Input, request: Request) -> Output:
        pass

    async def handle_request(self, request: Request) -> Response:
        try:
            # input data from request based on type
            input_data: Input = {}
            if request.is_json:
                try:
                    if request.data:  # Check if there's any data
                        input_data = request.get_json()
                    # If empty or not valid JSON, use empty dict
                except Exception as e:
                    # Log the error and return structured error response
                    PrintStyle().error(f"Invalid JSON in request: {str(e)}")
                    return Response(
                        response=json.dumps({
                            "error": "Invalid JSON format",
                            "message": "The request body contains invalid JSON",
                            "timestamp": time.time()
                        }),
                        status=400,
                        mimetype="application/json"
                    )
            else:
                input_data = {"data": request.get_data(as_text=True)}

            # Validate input data
            if not isinstance(input_data, dict):
                return Response(
                    response=json.dumps({
                        "error": "Invalid input format",
                        "message": "Input data must be a JSON object",
                        "timestamp": time.time()
                    }),
                    status=400,
                    mimetype="application/json"
                )

            # process via handler
            output = await self.process(input_data, request)

            # return output based on type
            if isinstance(output, Response):
                return output
            else:
                response_json = json.dumps(output)
                return Response(response=response_json, status=200, mimetype="application/json")

            # return exceptions with structured error response
        except Exception as e:
            error = format_error(e)
            PrintStyle.error(f"API error: {error}")
            return Response(
                response=json.dumps({
                    "error": "Internal server error",
                    "message": "An unexpected error occurred while processing the request",
                    "details": str(e) if hasattr(e, '__str__') else "Unknown error",
                    "timestamp": time.time()
                }),
                status=500,
                mimetype="application/json"
            )

    # get context to run agent zero in
    def get_context(self, ctxid: str):
        with self.thread_lock:
            if not ctxid:
                first = AgentContext.first()
                if first:
                    return first
                return AgentContext(config=initialize_agent())
            got = AgentContext.get(ctxid)
            if got:
                return got
            return AgentContext(config=initialize_agent(), id=ctxid)
