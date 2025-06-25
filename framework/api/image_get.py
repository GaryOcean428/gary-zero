import os

from flask import send_file

from framework.helpers import files
from framework.helpers.api import ApiHandler, Input, Output, Request


class ImageGet(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        # input data
        path = input.get("path", request.args.get("path", ""))
        if not path:
            raise ValueError("No path provided")

        # check if path is within base directory
        if not files.is_in_base_dir(path):
            raise ValueError("Path is outside of allowed directory")

        # check if file has an image extension
        # list of allowed image extensions
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]
        # get file extension
        file_ext = os.path.splitext(path)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValueError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )

        # check if file exists
        if not os.path.exists(path):
            raise ValueError("File not found")

        # send file
        return send_file(path)
