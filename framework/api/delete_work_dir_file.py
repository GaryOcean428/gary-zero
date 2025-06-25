from framework.api import get_work_dir_files
from framework.helpers import runtime
from framework.helpers.api import ApiHandler, Input, Output, Request
from framework.helpers.file_browser import FileBrowser


class DeleteWorkDirFile(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        file_path = input_data.get("path", "")
        if not file_path.startswith("/"):
            file_path = f"/{file_path}"

        current_path = input_data.get("currentPath", "")

        # browser = FileBrowser()
        res = await runtime.call_development_function(delete_file, file_path)

        if res:
            # Get updated file list
            # result = browser.get_files(current_path)
            result = await runtime.call_development_function(
                get_work_dir_files.get_files, current_path
            )
            return {"data": result}
        else:
            raise Exception("File not found or could not be deleted")


async def delete_file(file_path: str):
    browser = FileBrowser()
    return browser.delete_file(file_path)
