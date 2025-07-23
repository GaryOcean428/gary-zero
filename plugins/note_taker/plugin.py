"""Note taker plugin for Gary-Zero."""

from datetime import datetime

from framework.helpers.tool import Response, Tool
BaseClass = Tool


class NoteTaker(BaseClass):
    """Personal note management tool."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # In a real implementation, this would persist to a file
        self._notes = {
            "1": {
                "id": "1",
                "title": "Sample Note",
                "content": "This is a sample note to demonstrate the note taker.",
                "tags": ["sample", "demo"],
                "created": "2025-01-01T12:00:00",
                "modified": "2025-01-01T12:00:00"
            }
        }
        self._next_id = 2

    async def execute(self, **kwargs) -> Response:
        """Execute note operations."""

        action = self.args.get("action", "list").lower()

        if action == "create":
            return await self._create_note()
        elif action == "list":
            return await self._list_notes()
        elif action == "read":
            return await self._read_note()
        elif action == "update":
            return await self._update_note()
        elif action == "delete":
            return await self._delete_note()
        elif action == "search":
            return await self._search_notes()
        else:
            return Response(
                message=f"Unknown note action: {action}. Available: create, list, read, update, delete, search",
                break_loop=False
            )

    async def _create_note(self) -> Response:
        """Create a new note."""
        title = self.args.get("title", "Untitled Note")
        content = self.args.get("content", "")
        tags = self.args.get("tags", "").split(",") if self.args.get("tags") else []
        tags = [tag.strip() for tag in tags if tag.strip()]

        note_id = str(self._next_id)
        self._next_id += 1

        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "tags": tags,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }

        self._notes[note_id] = note

        response = "📝 Note created successfully!\n"
        response += f"ID: {note_id}\n"
        response += f"Title: {title}\n"
        response += f"Tags: {', '.join(tags) if tags else 'None'}\n"
        response += f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        return Response(message=response, break_loop=False)

    async def _list_notes(self) -> Response:
        """List all notes."""
        if not self._notes:
            return Response(
                message="📝 No notes found. Create your first note!",
                break_loop=False
            )

        response = f"📚 Your Notes ({len(self._notes)} total):\n\n"

        for note in sorted(self._notes.values(), key=lambda x: x['modified'], reverse=True):
            response += f"🗒️ #{note['id']}: {note['title']}\n"
            response += f"   Modified: {note['modified'][:19].replace('T', ' ')}\n"
            if note['tags']:
                response += f"   Tags: {', '.join(note['tags'])}\n"
            response += f"   Content: {note['content'][:50]}{'...' if len(note['content']) > 50 else ''}\n\n"

        return Response(message=response.strip(), break_loop=False)

    async def _read_note(self) -> Response:
        """Read a specific note."""
        note_id = self.args.get("id", "")

        if not note_id:
            return Response(
                message="❌ Note ID is required. Use: read with id parameter",
                break_loop=False
            )

        note = self._notes.get(note_id)
        if not note:
            return Response(
                message=f"❌ Note with ID '{note_id}' not found",
                break_loop=False
            )

        response = f"📖 Note #{note['id']}: {note['title']}\n\n"
        response += f"📅 Created: {note['created'][:19].replace('T', ' ')}\n"
        response += f"📅 Modified: {note['modified'][:19].replace('T', ' ')}\n"

        if note['tags']:
            response += f"🏷️ Tags: {', '.join(note['tags'])}\n"

        response += f"\n📄 Content:\n{note['content']}"

        return Response(message=response, break_loop=False)

    async def _update_note(self) -> Response:
        """Update an existing note."""
        note_id = self.args.get("id", "")

        if not note_id:
            return Response(
                message="❌ Note ID is required. Use: update with id parameter",
                break_loop=False
            )

        note = self._notes.get(note_id)
        if not note:
            return Response(
                message=f"❌ Note with ID '{note_id}' not found",
                break_loop=False
            )

        # Update fields if provided
        if "title" in self.args:
            note['title'] = self.args['title']

        if "content" in self.args:
            note['content'] = self.args['content']

        if "tags" in self.args:
            tags = self.args['tags'].split(",") if self.args['tags'] else []
            note['tags'] = [tag.strip() for tag in tags if tag.strip()]

        note['modified'] = datetime.now().isoformat()

        response = f"✅ Note #{note_id} updated successfully!\n"
        response += f"Title: {note['title']}\n"
        response += f"Modified: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        return Response(message=response, break_loop=False)

    async def _delete_note(self) -> Response:
        """Delete a note."""
        note_id = self.args.get("id", "")

        if not note_id:
            return Response(
                message="❌ Note ID is required. Use: delete with id parameter",
                break_loop=False
            )

        note = self._notes.get(note_id)
        if not note:
            return Response(
                message=f"❌ Note with ID '{note_id}' not found",
                break_loop=False
            )

        title = note['title']
        del self._notes[note_id]

        return Response(
            message=f"🗑️ Note #{note_id} '{title}' deleted successfully",
            break_loop=False
        )

    async def _search_notes(self) -> Response:
        """Search notes by content or tags."""
        query = self.args.get("query", "").lower()

        if not query:
            return Response(
                message="❌ Search query is required. Use: search with query parameter",
                break_loop=False
            )

        matches = []

        for note in self._notes.values():
            # Search in title, content, and tags
            if (query in note['title'].lower() or
                query in note['content'].lower() or
                any(query in tag.lower() for tag in note['tags'])):
                matches.append(note)

        if not matches:
            return Response(
                message=f"🔍 No notes found matching '{query}'",
                break_loop=False
            )

        response = f"🔍 Search results for '{query}' ({len(matches)} found):\n\n"

        for note in sorted(matches, key=lambda x: x['modified'], reverse=True):
            response += f"🗒️ #{note['id']}: {note['title']}\n"
            response += f"   Modified: {note['modified'][:19].replace('T', ' ')}\n"
            if note['tags']:
                response += f"   Tags: {', '.join(note['tags'])}\n"
            response += f"   Preview: {note['content'][:50]}{'...' if len(note['content']) > 50 else ''}\n\n"

        return Response(message=response.strip(), break_loop=False)
