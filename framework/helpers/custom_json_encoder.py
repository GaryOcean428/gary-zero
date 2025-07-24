"""Custom JSON encoder for handling complex data types."""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle special types like dataclasses, datetime,
    Enum, and sets.
    """

    def default(self, o):
        """
        Override default method to handle custom types.
        """
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, set):
            return list(o)
        if isinstance(o, UUID):
            return str(o)
        try:
            return super().default(o)
        except TypeError:
            # For any other un-serializable object, represent it as a string
            return str(o)
