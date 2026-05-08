"""
Parser for kernel panic and crash logs.
"""

import re
from typing import List, Optional, Tuple
from .base_parser import BaseParser, LogEvent
from ..utils import extract_subsystem, get_error_level


class PanicParser(BaseParser):
    """Parser for kernel panic and crash traces."""

    PANIC_PATTERNS = [
        re.compile(r"kernel\s+panic\s+-?\s*not\s+syncing", re.IGNORECASE),
        re.compile(r"BUG:\s+soft\s+lockup", re.IGNORECASE),
        re.compile(r"BUG:\s+hard\s+lockup", re.IGNORECASE),
        re.compile(r"general\s+protection\s+fault", re.IGNORECASE),
        re.compile(r"segmentation\s+fault", re.IGNORECASE),
        re.compile(r"page\s+fault", re.IGNORECASE),
        re.compile(r"double\s+fault", re.IGNORECASE),
        re.compile(r"stack\s+overflow", re.IGNORECASE),
        re.compile(r"watchdog:\s+BUG", re.IGNORECASE),
        re.compile(r"rcu_sched\s+self-detected\s+stall", re.IGNORECASE),
    ]

    STACK_TRACE_PATTERN = re.compile(r"Call\s+Trace:|Stack:|Backtrace:", re.IGNORECASE)
    RIP_PATTERN = re.compile(r"RIP:\s+0033:\[<([0-9a-f]+)>\]|PC\s+is\s+at\s+([0-9a-f]+)", re.IGNORECASE)
    REGISTER_PATTERN = re.compile(r"RAX:\s+[0-9a-f]+\s+RBX:\s+[0-9a-f]+", re.IGNORECASE)

    def detect_log_type(self, content: str) -> bool:
        """Check if content contains kernel panic."""
        for pattern in self.PANIC_PATTERNS:
            if pattern.search(content):
                return True
        return False

    def parse(self, content: str) -> List[LogEvent]:
        """
        Parse kernel panic log content.

        Args:
            content: Raw panic log content

        Returns:
            List of parsed LogEvent objects
        """
        self.events = []
        lines = content.split("\n")

        in_stack_trace = False
        current_panic_start = None

        for line_num, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            if self._is_panic_line(line):
                if current_panic_start is None:
                    current_panic_start = line_num
                in_stack_trace = True

            if self.STACK_TRACE_PATTERN.search(line):
                in_stack_trace = True

            event = self._parse_line(line, line_num, in_stack_trace)
            if event:
                self.events.append(event)

            if not line.strip():
                in_stack_trace = False

        self._extract_panic_info()
        self._extract_metadata()
        return self.events

    def _is_panic_line(self, line: str) -> bool:
        """Check if line indicates a panic."""
        for pattern in self.PANIC_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def _parse_line(self, line: str, line_num: int, in_stack_trace: bool) -> Optional[LogEvent]:
        """Parse a single panic log line."""
        level = "critical" if self._is_panic_line(line) else get_error_level(line)

        subsystem = extract_subsystem(line)
        if level == "critical":
            subsystem = "kernel"

        driver = self._extract_function_name(line)
        message = line.strip()
        tags = self._extract_tags(line, in_stack_trace)

        timestamp = None
        ts_match = re.search(r"\[\s*(\d+\.\d+)\]", line)
        if ts_match:
            timestamp = float(ts_match.group(1))

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

    def _extract_function_name(self, line: str) -> Optional[str]:
        """Extract function name from line."""
        match = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)\+0x[0-9a-f]+", line)
        if match:
            return match.group(1)

        match = re.search(r"<([a-zA-Z_][a-zA-Z0-9_]*)>", line)
        if match:
            return match.group(1)

        return None

    def _extract_tags(self, line: str, in_stack_trace: bool) -> List[str]:
        """Extract tags from panic log line."""
        tags = []

        if self._is_panic_line(line):
            tags.append("panic")

        if in_stack_trace:
            tags.append("stack_trace")

        if self.RIP_PATTERN.search(line):
            tags.append("crash_address")

        if self.REGISTER_PATTERN.search(line):
            tags.append("registers")

        line_lower = line.lower()
        if "soft lockup" in line_lower:
            tags.append("soft_lockup")
        if "hard lockup" in line_lower:
            tags.append("hard_lockup")
        if "segmentation fault" in line_lower:
            tags.append("segfault")
        if "general protection" in line_lower:
            tags.append("gpf")

        return tags

    def _extract_panic_info(self) -> None:
        """Extract specific panic information."""
        panic_info = {
            "panic_type": None,
            "crash_address": None,
            "stack_trace": [],
            "registers": {},
        }

        for event in self.events:
            if event.level == "critical" and not panic_info["panic_type"]:
                if "soft lockup" in event.message.lower():
                    panic_info["panic_type"] = "soft_lockup"
                elif "hard lockup" in event.message.lower():
                    panic_info["panic_type"] = "hard_lockup"
                elif "segmentation fault" in event.message.lower():
                    panic_info["panic_type"] = "segfault"
                elif "general protection" in event.message.lower():
                    panic_info["panic_type"] = "gpf"
                elif "kernel panic" in event.message.lower():
                    panic_info["panic_type"] = "kernel_panic"

            rip_match = self.RIP_PATTERN.search(event.message)
            if rip_match:
                panic_info["crash_address"] = rip_match.group(1) or rip_match.group(2)

            if "stack_trace" in event.tags:
                panic_info["stack_trace"].append(event.message)

            if "registers" in event.tags:
                reg_matches = re.findall(r"([A-Z]{3}):\s+([0-9a-f]+)", event.message)
                for reg, value in reg_matches:
                    panic_info["registers"][reg] = value

        self.metadata["panic_info"] = panic_info

    def _extract_metadata(self) -> None:
        """Extract metadata from parsed events."""
        if not self.events:
            return

        self.metadata["level_counts"] = self.get_event_count_by_level()

        subsystem_counts = {}
        for event in self.events:
            subsystem_counts[event.subsystem] = subsystem_counts.get(event.subsystem, 0) + 1
        self.metadata["subsystem_counts"] = subsystem_counts

        start, end = self.get_time_range()
        self.metadata["time_range"] = (start, end)
        if start and end:
            self.metadata["duration"] = end - start

"""
Panic parser module for kernel panic detection with stack trace and register extraction.
"""
