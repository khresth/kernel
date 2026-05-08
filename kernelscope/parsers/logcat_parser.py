"""
Parser for Android logcat logs.
"""

import re
from datetime import datetime
from typing import List, Optional
from .base_parser import BaseParser, LogEvent
from ..utils import extract_subsystem, get_error_level
from ..config import LOGCAT_SEVERITY


class LogcatParser(BaseParser):
    """Parser for Android logcat logs."""

    TIMESTAMP_PATTERN = re.compile(r"(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})")
    LOGCAT_PATTERN = re.compile(
        r"(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+(\S+)\s+([VDIWEF])\s+(.*)"
    )
    SIMPLE_PATTERN = re.compile(r"([VDIWEF])\/(\S+)\(\s*\d+\):\s*(.*)")

    def detect_log_type(self, content: str) -> bool:
        """Check if content is logcat format."""
        if self.LOGCAT_PATTERN.search(content):
            return True
        if self.TIMESTAMP_PATTERN.search(content):
            return True
        if re.search(r"[VDIWEF]/", content):
            return True
        return False

    def parse(self, content: str) -> List[LogEvent]:
        """
        Parse logcat log content.

        Args:
            content: Raw logcat log content

        Returns:
            List of parsed LogEvent objects
        """
        self.events = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            event = self._parse_line(line, line_num)
            if event:
                self.events.append(event)

        self._extract_metadata()
        return self.events

    def _parse_line(self, line: str, line_num: int) -> Optional[LogEvent]:
        """Parse a single logcat line."""
        match = self.LOGCAT_PATTERN.match(line)
        if match:
            return self._parse_full_line(match, line, line_num)

        match = self.SIMPLE_PATTERN.match(line)
        if match:
            return self._parse_simple_line(match, line, line_num)

        return self._parse_fallback(line, line_num)

    def _parse_full_line(self, match: re.Match, line: str, line_num: int) -> LogEvent:
        """Parse a full logcat line with all fields."""
        timestamp_str = match.group(1)
        pid = match.group(2)
        tid = match.group(3)
        tag = match.group(4)
        severity = match.group(5)
        message = match.group(6)

        timestamp = None
        try:
            dt = datetime.strptime(timestamp_str, "%m-%d %H:%M:%S.%f")
            dt = dt.replace(year=datetime.now().year)
            timestamp = dt.timestamp()
        except ValueError:
            pass

        level = LOGCAT_SEVERITY.get(severity, "info").lower()
        subsystem = extract_subsystem(tag) or extract_subsystem(message)
        driver = tag if len(tag) < 50 else None
        tags = self._extract_tags(tag, message, level)

        return LogEvent(
            timestamp=timestamp,
            level=level,
            subsystem=subsystem,
            driver=driver,
            message=message,
            raw_line=line,
            line_number=line_num,
            tags=tags,
        )

    def _parse_simple_line(self, match: re.Match, line: str, line_num: int) -> LogEvent:
        """Parse a simple logcat line."""
        severity = match.group(1)
        tag = match.group(2)
        message = match.group(3)

        level = LOGCAT_SEVERITY.get(severity, "info").lower()
        subsystem = extract_subsystem(tag) or extract_subsystem(message)
        driver = tag if len(tag) < 50 else None
        tags = self._extract_tags(tag, message, level)

        return LogEvent(
            timestamp=None,
            level=level,
            subsystem=subsystem,
            driver=driver,
            message=message,
            raw_line=line,
            line_number=line_num,
            tags=tags,
        )

    def _parse_fallback(self, line: str, line_num: int) -> Optional[LogEvent]:
        """Parse line using fallback method."""
        level = get_error_level(line)
        subsystem = extract_subsystem(line)

        return LogEvent(
            timestamp=None,
            level=level,
            subsystem=subsystem,
            driver=None,
            message=line,
            raw_line=line,
            line_number=line_num,
            tags=[],
        )

    def _extract_tags(self, tag: str, message: str, level: str) -> List[str]:
        """Extract tags from logcat fields."""
        tags = []
        tags.append(level)

        tag_lower = tag.lower()
        if "activity" in tag_lower or "activitymanager" in tag_lower:
            tags.append("activity")
        if "surface" in tag_lower:
            tags.append("graphics")
        if "audio" in tag_lower:
            tags.append("audio")
        if "camera" in tag_lower:
            tags.append("camera")
        if "wifi" in tag_lower:
            tags.append("network")
        if "bluetooth" in tag_lower:
            tags.append("bluetooth")
        if "power" in tag_lower:
            tags.append("power")
        if "thermal" in tag_lower:
            tags.append("thermal")

        msg_lower = message.lower()
        if "crash" in msg_lower or "fatal" in msg_lower:
            tags.append("crash")
        if "anr" in msg_lower:
            tags.append("anr")

        return tags

    def _extract_metadata(self) -> None:
        """Extract metadata from parsed events."""
        if not self.events:
            return

        self.metadata["level_counts"] = self.get_event_count_by_level()

        tag_counts = {}
        for event in self.events:
            if event.driver:
                tag_counts[event.driver] = tag_counts.get(event.driver, 0) + 1
        self.metadata["tag_counts"] = tag_counts

        start, end = self.get_time_range()
        self.metadata["time_range"] = (start, end)
        if start and end:
            self.metadata["duration"] = end - start

"""
Logcat parser module for Android logs with severity mapping and tag extraction.
"""
