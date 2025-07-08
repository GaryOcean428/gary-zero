"""Runtime configuration and utilities for the application."""

from __future__ import annotations

# Standard library imports
import argparse
import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, overload

# Local application imports
from . import rfc

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class RuntimeState:
    """Singleton class to manage runtime state and command line arguments."""

    _instance: RuntimeState | None = None
    args: dict[str, Any] = field(default_factory=dict)
    dockerman: Any = None
    _parser: argparse.ArgumentParser = field(default_factory=argparse.ArgumentParser)
    _initialized: bool = False

    def __post_init__(self):
        if not self._initialized:
            self._initialize_parser()
            self._initialized = True

    def _initialize_parser(self) -> None:
        """Initialize the argument parser with all supported arguments."""
        self._parser.add_argument("--port", type=int, default=None, help="Web UI port")
        self._parser.add_argument("--host", type=str, default=None, help="Web UI host")
        self._parser.add_argument(
            "--cloudflare_tunnel",
            type=bool,
            default=False,
            help="Use cloudflare tunnel for public URL",
        )
        self._parser.add_argument(
            "--development", type=bool, default=False, help="Development mode"
        )
        # Add other arguments as needed

    def parse_args(self) -> dict[str, Any]:
        """Parse command line arguments if not already done.

        Returns:
            Dictionary of parsed arguments.
        """
        if not hasattr(self, "_args") or not self._args:
            self._args = vars(self._parser.parse_args())
        return self._args

    @classmethod
    def get_instance(cls) -> RuntimeState:
        """Get the singleton instance of RuntimeState."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def initialize() -> None:
    """Initialize the runtime state by parsing command line arguments."""
    RuntimeState.get_instance().parse_args()


def get_arg(name: str, default: Any = None) -> Any:
    """Get a command line argument by name with an optional default value.

    Args:
        name: The name of the argument to retrieve.
        default: The default value to return if the argument is not found.

    Returns:
        The value of the argument if it exists, otherwise the default value.
    """
    return RuntimeState.get_instance().parse_args().get(name, default)


def has_arg(name: str) -> bool:
    """Check if a command line argument exists.

    Args:
        name: The name of the argument to check.

    Returns:
        True if the argument exists, False otherwise.
    """
    return name in RuntimeState.get_instance().parse_args()


def is_dockerized() -> bool:
    """Check if running in a Docker container."""
    return os.path.exists("/.dockerenv")


def is_development() -> bool:
    """Check if running in development mode."""
    return get_arg("development", False)


def get_local_url() -> str:
    """Get the local URL based on the runtime environment."""
    host = get_arg("host", "0.0.0.0")
    port = get_arg("port", 8000)
    return f"http://{host}:{port}"


@overload
async def call_development_function(
    func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any
) -> T: ...


@overload
async def call_development_function(func: Callable[..., T], *args: Any, **kwargs: Any) -> T: ...


async def call_development_function(
    func: Callable[..., T] | Callable[..., Awaitable[T]], *args: Any, **kwargs: Any
) -> T:
    """Call a function either locally or remotely based on the environment."""
    if is_development():
        url = _get_rfc_url()
        password = _get_rfc_password()
        result = await rfc.call_rfc(
            url=url,
            password=password,
            module=func.__module__,
            function_name=func.__name__,
            args=list(args),
            kwargs=kwargs,
        )
        return result

    # Local execution
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)  # type: ignore
    return func(*args, **kwargs)  # type: ignore


def handle_rfc(rfc_call: rfc.RFCCall) -> None:
    """Handle an incoming RFC call."""
    # Implementation here
    pass


def _get_rfc_password() -> str:
    """Get the RFC password from environment variables."""
    password = os.getenv("RFC_PASSWORD")
    if not password:
        raise ValueError("RFC_PASSWORD environment variable not set")
    return password


def _get_rfc_url() -> str:
    """Get the RFC URL from settings."""
    # Implementation here
    return "http://localhost:8000"  # Default URL


def call_development_function_sync(
    func: Callable[..., T] | Callable[..., Awaitable[T]], *args: Any, **kwargs: Any
) -> T:
    """Synchronously call a function that might be async."""
    if asyncio.iscoroutinefunction(func):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))  # type: ignore
    return func(*args, **kwargs)  # type: ignore


def get_web_ui_port() -> int:
    """Get the web UI port from args or environment."""
    return get_arg("port", 8000)


def get_tunnel_api_port() -> int:
    """Get the tunnel API port from args or environment."""
    return int(os.getenv("TUNNEL_API_PORT", "4040"))
