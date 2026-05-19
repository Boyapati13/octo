"""Base channel class for OCTO messaging gateway."""
from __future__ import annotations
import logging
import threading
from abc import ABC, abstractmethod
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class BaseChannel(ABC):
    """Abstract base for all OCTO messaging channels."""

    def __init__(self, name: str, config: dict):
        self.name        = name
        self.config      = config
        self._running    = False
        self._on_message: Optional[Callable[[str, str, str], None]] = None  # (channel, user_id, text)
        self._thread: Optional[threading.Thread] = None

    def on_message(self, handler: Callable[[str, str, str], None]) -> None:
        """Register callback: handler(channel_name, user_id, text)."""
        self._on_message = handler

    def _emit(self, user_id: str, text: str) -> None:
        if self._on_message:
            try:
                self._on_message(self.name, user_id, text)
            except Exception as e:
                logger.error("[%s] Message handler error: %s", self.name, e)

    @abstractmethod
    def start(self) -> None:
        """Start the channel listener."""

    @abstractmethod
    def send(self, user_id: str, text: str) -> None:
        """Send a reply to a user."""

    def stop(self) -> None:
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
