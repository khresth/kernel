"""
Base parser class for all log parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogEvent:
    """Represents a single parsed log event."""
    timestamp: Optional[float]
    level: str
    subsystem: str
    driver: Optional[str]
    message: str
    raw_line: str
    line_number: int
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "subsystem": self.subsystem,
            "driver": self.driver,
            "message": self.message,
            "raw_line": self.raw_line,
            "line_number": self.line_number,
            "tags": self.tags,
        }


class BaseParser(ABC):
    """Abstract base class for log parsers."""

    def __init__(self):
        self.events: List[LogEvent] = []
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def parse(self, content: str) -> List[LogEvent]:
        """
        Parse log content into events.

        Args:
            content: Raw log content

        Returns:
            List of parsed LogEvent objects
        """
        pass

    @abstractmethod
    def detect_log_type(self, content: str) -> bool:
        """
        Check if content matches this parser's log type.

        Args:
            content: Raw log content

        Returns:
            True if content matches this parser type
        """
        pass

    def get_events(self) -> List[LogEvent]:
        """Return parsed events."""
        return self.events

    def get_metadata(self) -> Dict[str, Any]:
        """Return parser metadata."""
        return self.metadata

    def filter_by_level(self, level: str) -> List[LogEvent]:
        """Filter events by error level."""
        return [e for e in self.events if e.level == level]

    def filter_by_subsystem(self, subsystem: str) -> List[LogEvent]:
        """Filter events by subsystem."""
        return [e for e in self.events if e.subsystem == subsystem]

    def filter_by_driver(self, driver: str) -> List[LogEvent]:
        """Filter events by driver name."""
        return [e for e in self.events if e.driver == driver]

    def get_time_range(self) -> tuple[Optional[float], Optional[float]]:
        """Get start and end timestamps."""
        timestamps = [e.timestamp for e in self.events if e.timestamp is not None]
        if not timestamps:
            return (None, None)
        return (min(timestamps), max(timestamps))

    def get_event_count_by_level(self) -> Dict[str, int]:
        """Count events by level."""
        counts = {}
        for event in self.events:
            counts[event.level] = counts.get(event.level, 0) + 1
        return counts

"""
Base parser module providing abstract class and data structures for log parsing.
"""
