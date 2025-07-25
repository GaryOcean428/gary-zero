from framework.helpers import runtime
from framework.helpers.api import ApiHandler, Input, Output, Request
from framework.helpers.file_browser import FileBrowser


class GetWorkDirFiles(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        current_path = request.args.get("path", "")
        if current_path == "$WORK_DIR":
            # if runtime.is_development():
            #     current_path = "work_dir"
            # else:
            #     current_path = "root"
            current_path = "root"

        # browser = FileBrowser()
        # result = browser.get_files(current_path)
        result = await runtime.call_development_function(get_files, current_path)

        return {"data": result}


async def get_files(path):
    browser = FileBrowser()
    return browser.get_files(path)
