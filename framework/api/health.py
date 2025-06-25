from framework.helpers import errors, git
from framework.helpers.api import ApiHandler, Input, Output, Request


class HealthCheck(ApiHandler):

    async def process(self, input_data: Input, request: Request) -> Output:
        gitinfo = None
        error = None
        try:
            gitinfo = git.get_git_info()
        except Exception as e:
            error = errors.error_text(e)

        return {"gitinfo": gitinfo, "error": error}
