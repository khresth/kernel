"""
Parser for Linux dmesg logs.
"""

import re
from typing import List, Optional
from .base_parser import BaseParser, LogEvent
from ..utils import extract_subsystem, extract_driver_name, get_error_level


class DmesgParser(BaseParser):
    """Parser for Linux kernel ring buffer (dmesg) logs."""

    TIMESTAMP_PATTERN = re.compile(r"\[\s*(\d+\.\d+)\]")
    FACILITY_PATTERN = re.compile(r"<(\d)>")
    SUBSYSTEM_PATTERN = re.compile(r"(\w+_\w+|\w+driver|\w+):\s+")

    def detect_log_type(self, content: str) -> bool:
        """Check if content is dmesg format."""
        if self.TIMESTAMP_PATTERN.search(content):
            return True
        if re.search(r"kernel:\s*\[", content):
            return True
        return False

    def parse(self, content: str) -> List[LogEvent]:
        """
        Parse dmesg log content.

        Args:
            content: Raw dmesg log content

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
        """Parse a single dmesg line."""
        timestamp = None
        ts_match = self.TIMESTAMP_PATTERN.search(line)
        if ts_match:
            timestamp = float(ts_match.group(1))

        level = "info"
        fac_match = self.FACILITY_PATTERN.search(line)
        if fac_match:
            facility = int(fac_match.group(1))
            level_code = facility & 0x07
            level_map = {
                0: "emerg",
                1: "alert",
                2: "crit",
                3: "error",
                4: "warning",
                5: "notice",
                6: "info",
                7: "debug",
            }
            level = level_map.get(level_code, "info")
        else:
            level = get_error_level(line)

        subsystem = extract_subsystem(line)
        driver = extract_driver_name(line)

        message = line
        if ts_match:
            message = message.replace(ts_match.group(0), "")
        if fac_match:
            message = message.replace(fac_match.group(0), "")
        message = message.strip()

        tags = self._extract_tags(line)

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

    def _extract_tags(self, line: str) -> List[str]:
        """Extract tags from log line."""
        tags = []

        if any(keyword in line.lower() for keyword in ["boot", "init", "start"]):
            tags.append("boot")

        if any(keyword in line.lower() for keyword in ["driver", "probe", "load"]):
            tags.append("driver")

        if any(keyword in line.lower() for keyword in ["error", "fail", "panic"]):
            tags.append("error")

        if any(keyword in line.lower() for keyword in ["pci", "usb", "acpi", "i2c", "spi"]):
            tags.append("hardware")

        if any(keyword in line.lower() for keyword in ["network", "eth", "wifi", "bluetooth"]):
            tags.append("network")

        return tags

    def _extract_metadata(self) -> None:
        """Extract metadata from parsed events."""
        if not self.events:
            return

        self.metadata["level_counts"] = self.get_event_count_by_level()

        subsystem_counts = {}
        for event in self.events:
            subsystem_counts[event.subsystem] = subsystem_counts.get(event.subsystem, 0) + 1
        self.metadata["subsystem_counts"] = subsystem_counts

        for event in self.events:
            if "Linux version" in event.message:
                version_match = re.search(r"Linux version (\S+)", event.message)
                if version_match:
                    self.metadata["kernel_version"] = version_match.group(1)
                    break

        start, end = self.get_time_range()
        self.metadata["time_range"] = (start, end)
        if start and end:
            self.metadata["duration"] = end - start

"""
Dmesg parser module for Linux kernel ring buffer logs with timestamp and facility extraction.
"""
