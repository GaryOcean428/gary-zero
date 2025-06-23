import os

from werkzeug.utils import secure_filename

from zero.helpers import files, memory
from zero.helpers.api import ApiHandler, Input, Output, Request


class ImportKnowledge(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        if "files[]" not in request.files:
            raise Exception("No files part")

        ctxid = request.form.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")

        context = self.get_context(ctxid)

        file_list = request.files.getlist("files[]")
        knowledge_folder = files.get_abs_path(
            memory.get_custom_knowledge_subdir_abs(context.agent0), "main"
        )

        saved_filenames = []

        for file in file_list:
            if file:
                filename = secure_filename(file.filename)  # type: ignore
                file.save(os.path.join(knowledge_folder, filename))
                saved_filenames.append(filename)

        # reload memory to re-import knowledge
        await memory.Memory.reload(context.agent0)
        context.log.set_initial_progress()

        return {"message": "Knowledge Imported", "filenames": saved_filenames[:5]}
