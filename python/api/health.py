from python.helpers import errors, git
from python.helpers.api import ApiHandler, Input, Output, Request


class HealthCheck(ApiHandler):

    async def process(self, input: Input, request: Request) -> Output:
        gitinfo = None
        error = None
        try:
            gitinfo = git.get_git_info()
        except Exception as e:
            error = errors.error_text(e)

        return {"gitinfo": gitinfo, "error": error}
