"""Proxy module to expose model utilities from the sibling ``models.py``.

This package-level ``__init__`` acts as a thin wrapper around the single
``models.py`` module located one directory up from this package.  Without this
wrapper Python's import system would resolve ``import models`` to this package
and then recursively attempt to import itself when trying to bring in the
symbols from ``models.py``.  That recursion resulted in the fallback branch
below being executed and meant ``get_model`` always returned ``None``.

To avoid that naming conflict we bypass the normal module resolution and load
``models.py`` directly via ``importlib``.  If that file cannot be imported for
any reason we fall back to lightweight stubs that allow the rest of the code
to import this package without crashing, albeit without functional model
support.
"""

from __future__ import annotations

import importlib.util
import os
from enum import Enum
from types import ModuleType
from typing import Any, Callable, Optional

_models_module: Optional[ModuleType] = None


def _load_models_module() -> Optional[ModuleType]:
    """Attempt to load the neighbouring ``models.py`` as a module.

    Returns:
        The loaded module if successful, otherwise ``None``.
    """
    global _models_module
    if _models_module is not None:
        return _models_module

    parent_dir = os.path.dirname(os.path.dirname(__file__))
    models_file = os.path.join(parent_dir, "models.py")
    if not os.path.isfile(models_file):
        return None

    spec = importlib.util.spec_from_file_location("gary_zero_models", models_file)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore[call-arg]
        except Exception:
            # If loading fails, do not cache failure; return None so fallback is used.
            return None
        _models_module = module
        return module
    return None


# Try to import the real models module; otherwise fall back to stubs.
_real = _load_models_module()
if _real is not None:
    # Export selected attributes from the real models module.
    ModelProvider = _real.ModelProvider  # type: ignore[attr-defined]
    ModelType = _real.ModelType  # type: ignore[attr-defined]
    get_api_key: Callable[[str], Optional[str]] = _real.get_api_key  # type: ignore[attr-defined]
    get_model: Callable[..., Any] = _real.get_model  # type: ignore[attr-defined]
    get_rate_limiter: Callable[..., Any] = _real.get_rate_limiter  # type: ignore[attr-defined]
    parse_chunk: Callable[[Any], str] = _real.parse_chunk  # type: ignore[attr-defined]
else:
    # Minimal stub implementations used when the real models module cannot be loaded.
    class ModelProvider(Enum):
        ANTHROPIC = "Anthropic"
        OPENAI = "OpenAI"
        GOOGLE = "Google"
        GROQ = "Groq"
        MISTRALAI = "Mistral AI"
        OTHER = "Other"

    class ModelType(Enum):
        CHAT = "Chat"
        EMBEDDING = "Embedding"

    def get_api_key(service: str) -> Optional[str]:
        return None

    def get_model(
        model_type: ModelType,
        provider: ModelProvider,
        name: str,
        **kwargs: Any,
    ) -> None:
        return None

    def get_rate_limiter(
        provider: ModelProvider,
        name: str,
        requests: int,
        input_tokens: int,
        output_tokens: int,
    ):
        from framework.helpers.rate_limiter import RateLimiter

        return RateLimiter(
            requests=requests or 1000,
            input_tokens=input_tokens or 1000000,
            output_tokens=output_tokens or 1000000,
        )

    def parse_chunk(chunk: Any) -> str:
        if isinstance(chunk, str):
            return chunk
        elif hasattr(chunk, "content"):
            return str(chunk.content)
        else:
            return str(chunk)
