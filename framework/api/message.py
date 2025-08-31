import os

from werkzeug.utils import secure_filename

from agent import AgentContext, UserMessage
from framework.helpers import files
from framework.helpers.api import ApiHandler, Input, Output, Request
from framework.helpers.defer import DeferredTask
from framework.helpers.print_style import PrintStyle


class Message(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        task, context = await self.communicate(input=input_data, request=request)
        return await self.respond(task, context)

    async def respond(self, task: DeferredTask, context: AgentContext):
        # Handle duplicate message case (task is None)
        if task is None:
            return {
                "message": "Duplicate message ignored",
                "context": context.id,
                "duplicate": True,
            }

        result = await task.result()  # type: ignore
        return {
            "message": result,
            "context": context.id,
        }

    async def communicate(self, input: dict, request: Request):
        # Handle both JSON and multipart/form-data
        if request.content_type.startswith("multipart/form-data"):
            text = request.form.get("text", "")
            ctxid = request.form.get("context", "")
            message_id = request.form.get("message_id", None)
            client_message_id = request.form.get("client_message_id", None)
            attachments = request.files.getlist("attachments")
            attachment_paths = []

            upload_folder_int = "/a0/tmp/uploads"
            upload_folder_ext = files.get_abs_path("tmp/uploads")

            if attachments:
                os.makedirs(upload_folder_ext, exist_ok=True)
                for attachment in attachments:
                    if attachment.filename is None:
                        continue
                    filename = secure_filename(attachment.filename)
                    save_path = files.get_abs_path(upload_folder_ext, filename)
                    attachment.save(save_path)
                    attachment_paths.append(os.path.join(upload_folder_int, filename))
        else:
            # Handle JSON request as before
            input_data = request.get_json()
            text = input_data.get("text", "")
            ctxid = input_data.get("context", "")
            message_id = input_data.get("message_id", None)
            client_message_id = input_data.get("client_message_id", None)
            # Also check Idempotency-Key header
            if not client_message_id:
                client_message_id = request.headers.get("Idempotency-Key", None)
            attachment_paths = []

        # Now process the message
        message = text

        # Obtain agent context
        context = self.get_context(ctxid)

        # Check for existing message with same client_message_id for idempotency
        if client_message_id:
            existing_logs = context.log.logs
            for log_item in existing_logs:
                if (
                    log_item.type == "user"
                    and log_item.kvps
                    and log_item.kvps.get("client_message_id") == client_message_id
                ):
                    # Return existing message result to prevent duplicate
                    PrintStyle(font_color="yellow").print(
                        f"🚫 Skipping duplicate message with client_message_id: {client_message_id}"
                    )
                    return None, context  # Return None to indicate duplicate

            # Also check if there's an in-progress message with the same client_message_id
            # This prevents race conditions during concurrent requests
            if hasattr(context, "_processing_messages"):
                if client_message_id in context._processing_messages:
                    PrintStyle(font_color="yellow").print(
                        f"🚫 Message already being processed: {client_message_id}"
                    )
                    return None, context
            else:
                context._processing_messages = set()

            # Mark this message as being processed
            context._processing_messages.add(client_message_id)

        try:
            # Store attachments in agent data
            # context.agent0.set_data("attachments", attachment_paths)

            # Prepare attachment filenames for logging
            attachment_filenames = (
                [os.path.basename(path) for path in attachment_paths]
                if attachment_paths
                else []
            )

            # Print to console and log
            PrintStyle(
                background_color="#6C3483", font_color="white", bold=True, padding=True
            ).print("User message:")
            PrintStyle(font_color="white", padding=False).print(f"> {message}")
            if attachment_filenames:
                PrintStyle(font_color="white", padding=False).print("Attachments:")
                for filename in attachment_filenames:
                    PrintStyle(font_color="white", padding=False).print(f"- {filename}")

            # Add client_message_id to kvps for deduplication
            log_kvps = {"attachments": attachment_filenames}
            if client_message_id:
                log_kvps["client_message_id"] = client_message_id

            # Log the message with message_id and attachments
            context.log.log(
                type="user",
                heading="User message",
                content=message,
                kvps=log_kvps,
                id=message_id,
            )

            return context.communicate(UserMessage(message, attachment_paths)), context
        finally:
            # Clean up processing state
            if client_message_id and hasattr(context, "_processing_messages"):
                context._processing_messages.discard(client_message_id)
