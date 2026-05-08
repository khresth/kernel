"""
Utility functions for KernelScope.
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


def detect_log_type(content: str) -> str:
    """
    Automatically detect log type from content.

    Args:
        content: Log file content

    Returns:
        Detected log type (dmesg, logcat, kernel_panic, boot, or unknown)
    """
    from .config import LOG_TYPES

    scores = {}
    for log_type, config in LOG_TYPES.items():
        score = 0
        for pattern in config.patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            score += matches
        scores[log_type] = score

    max_score = max(scores.values())
    if max_score == 0:
        return "unknown"

    return max(scores, key=scores.get)


def parse_timestamp(line: str) -> Optional[float]:
    """
    Extract timestamp from log line.

    Args:
        line: Log line

    Returns:
        Timestamp as float seconds, or None if not found
    """
    dmesg_match = re.search(r"\[\s*(\d+\.\d+)\]", line)
    if dmesg_match:
        return float(dmesg_match.group(1))

    logcat_match = re.search(r"(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})", line)
    if logcat_match:
        try:
            dt = datetime.strptime(logcat_match.group(1), "%m-%d %H:%M:%S.%f")
            return dt.timestamp()
        except ValueError:
            pass

    return None


def extract_subsystem(line: str) -> str:
    """
    Extract subsystem name from log line.

    Args:
        line: Log line

    Returns:
        Subsystem name or 'general'
    """
    from .config import KNOWN_SUBSYSTEMS

    line_lower = line.lower()
    for subsystem in KNOWN_SUBSYSTEMS:
        if subsystem.lower() in line_lower:
            return subsystem

    return "general"


def extract_driver_name(line: str) -> Optional[str]:
    """
    Extract driver/module name from log line.

    Args:
        line: Log line

    Returns:
        Driver name or None
    """
    match = re.search(r"(\w+_\w+|\w+driver|\w+_\d+):\s+", line)
    if match:
        return match.group(1)

    match = re.search(r"\[(\w+_\w+|\w+driver)\]", line)
    if match:
        return match.group(1)

    return None


def get_error_level(line: str) -> str:
    """
    Determine error level from log line.

    Args:
        line: Log line

    Returns:
        Error level (error, warning, info, debug)
    """
    line_lower = line.lower()

    error_keywords = ["error", "fail", "panic", "bug", "fatal", "critical", "exception"]
    warning_keywords = ["warning", "warn", "timeout", "retry", "deprecated"]

    for keyword in error_keywords:
        if keyword in line_lower:
            return "error"

    for keyword in warning_keywords:
        if keyword in line_lower:
            return "warning"

    return "info"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = seconds / 60
        return f"{minutes:.2f}m"


def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate string to maximum length with ellipsis.

    Args:
        text: Input string
        max_length: Maximum length

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Safely parse JSON string.

    Args:
        text: JSON string

    Returns:
        Parsed dictionary or empty dict on failure
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}


def write_report(content: str, output_path: str) -> None:
    """
    Write report content to file.

    Args:
        content: Report content
        output_path: Output file path
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def calculate_anomaly_score(events: List[Dict[str, Any]]) -> float:
    """
    Calculate anomaly score based on event patterns.

    Args:
        events: List of parsed events

    Returns:
        Anomaly score (0-100)
    """
    if not events:
        return 0.0

    error_count = sum(1 for e in events if e.get("level") == "error")
    warning_count = sum(1 for e in events if e.get("level") == "warning")
    total_count = len(events)

    if total_count == 0:
        return 0.0

    error_ratio = error_count / total_count
    warning_ratio = warning_count / total_count

    score = (error_ratio * 70) + (warning_ratio * 30)

    driver_failures = {}
    for event in events:
        driver = event.get("driver")
        if driver and event.get("level") == "error":
            driver_failures[driver] = driver_failures.get(driver, 0) + 1

    for count in driver_failures.values():
        if count > 3:
            score += 10

    return min(score, 100.0)

"""
Utility module for log type detection, timestamp parsing, and data processing.
"""
