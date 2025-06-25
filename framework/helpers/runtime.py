"""Runtime configuration and utilities for the application."""
from __future__ import annotations

# Standard library imports
import argparse
import asyncio
import inspect
import queue
import threading
import urllib.parse
from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, cast, overload

# Local application imports
from . import dotenv, rfc, settings

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
            "--development",
            type=bool,
            default=False,
            help="Development mode"
        )
        self._parser.add_argument(
            "--dockerized",
            action="store_true",
            help="Run in Docker container"
        )
        self._parser.add_argument(
            "--tunnel_api_port",
            type=int,
            default=None,
            help="Tunnel API port"
        )

    def parse_args(self) -> dict[str, Any]:
        """Parse command line arguments if not already done.

        Returns:
            Dictionary of parsed arguments.
        """
        if not self.args:
            known, unknown = self._parser.parse_known_args()
            self.args = vars(known)
            for arg in unknown:
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    key = key.lstrip("-")
                    self.args[key] = value
        return self.args

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
    return RuntimeState.get_instance().args.get(name, default)


def has_arg(name: str) -> bool:
    """Check if a command line argument exists.

    Args:
        name: The name of the argument to check.

    Returns:
        True if the argument exists, False otherwise.
    """
    return name in RuntimeState.get_instance().args


def is_dockerized() -> bool:
    """Check if running in a Docker container."""
    return bool(get_arg("dockerized"))


def is_development() -> bool:
    """Check if running in development mode."""
    return not is_dockerized()


def get_local_url() -> str:
    """Get the local URL based on the runtime environment."""
    if is_dockerized():
        return "host.docker.internal"
    return "127.0.0.1"


@overload
async def call_development_function(
    func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any
) -> T: ...


@overload
async def call_development_function(
    func: Callable[..., T], *args: Any, **kwargs: Any
) -> T: ...


async def call_development_function(
    func: Union[Callable[..., T], Callable[..., Awaitable[T]]], *args: Any, **kwargs: Any
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
        return cast(T, result)
    else:
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)  # type: ignore
        return func(*args, **kwargs)  # type: ignore


async def handle_rfc(rfc_call: rfc.RFCCall) -> Any:
    """Handle an incoming RFC call."""
    return await rfc.handle_rfc(rfc_call=rfc_call, password=_get_rfc_password())


def _get_rfc_password() -> str:
    """Get the RFC password from environment variables."""
    password = dotenv.get_dotenv_value(dotenv.KEY_RFC_PASSWORD)
    if not password:
        print(
            "Warning: No RFC password set. Using default password. "
            "RFC calls may not work properly."
        )
        return "default_rfc_password_change_me"
    return password


def _get_rfc_url() -> str:
    """Get the RFC URL from settings."""
    settings_dict = settings.get_settings()
    url = settings_dict["rfc_url"]

    # Ensure URL has scheme
    if "://" not in url:
        url = "http://" + url

    # Parse URL to handle ports properly
    parsed = urllib.parse.urlparse(url)

    # Only add port if not already in URL
    if not parsed.port:
        # Rebuild URL with port if not present
        netloc = f"{parsed.hostname}:{settings_dict['rfc_port_http']}" if parsed.hostname else ""
        parsed = parsed._replace(netloc=netloc)

    # Rebuild URL and ensure /rfc path
    url = urllib.parse.urlunparse(parsed)
    if not url.endswith('/rfc'):
        url = url.rstrip('/') + '/rfc'

    return url


def call_development_function_sync(
    func: Union[Callable[..., T], Callable[..., Awaitable[T]]], *args: Any, **kwargs: Any
) -> T:
    """Synchronously call a function that might be async."""
    result_queue: queue.Queue[T] = queue.Queue()

    def run_in_thread() -> None:
        result = asyncio.run(call_development_function(func, *args, **kwargs))
        result_queue.put(result)

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=30)

    if thread.is_alive():
        raise TimeoutError("Function call timed out after 30 seconds")

    return result_queue.get_nowait()


def get_web_ui_port() -> int:
    """Get the web UI port from args or environment."""
    port = get_arg("port") or int(dotenv.get_dotenv_value("WEB_UI_PORT", 0)) or 5000
    return int(port)


def get_tunnel_api_port() -> int:
    """Get the tunnel API port from args or environment."""
    port = get_arg("tunnel_api_port") or int(dotenv.get_dotenv_value("TUNNEL_API_PORT", 0)) or 55520
    return int(port)
