"""
Driver failure analyzer for detecting initialization failures.
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from ..parsers.base_parser import LogEvent
from ..config import DRIVER_FAILURE_PATTERNS


@dataclass
class DriverFailure:
    """Represents a driver failure event."""
    driver_name: str
    failure_type: str
    timestamp: Optional[float]
    message: str
    line_number: int
    retry_count: int = 0


class DriverFailureAnalyzer:
    """Analyzes driver initialization failures and suspicious modules."""

    def __init__(self, events: List[LogEvent]):
        """
        Initialize driver failure analyzer.

        Args:
            events: List of parsed log events
        """
        self.events = events
        self.failures: List[DriverFailure] = []
        self.suspicious_drivers: Set[str] = set()
        self._analyze()

    def _analyze(self) -> None:
        """Perform driver failure analysis."""
        driver_events = [e for e in self.events if e.driver]

        # Track driver retry attempts
        driver_attempts: Dict[str, List[LogEvent]] = {}
        for event in driver_events:
            if event.driver not in driver_attempts:
                driver_attempts[event.driver] = []
            driver_attempts[event.driver].append(event)

        # Detect failures
        for event in self.events:
            failure = self._detect_failure(event)
            if failure:
                # Count retries
                if failure.driver_name in driver_attempts:
                    failure.retry_count = len(driver_attempts[failure.driver_name])
                self.failures.append(failure)
                self.suspicious_drivers.add(failure.driver_name)

        # Identify drivers with repeated failures
        for driver, attempts in driver_attempts.items():
            error_count = sum(1 for e in attempts if e.level == "error")
            if error_count >= 3:
                self.suspicious_drivers.add(driver)

    def _detect_failure(self, event: LogEvent) -> Optional[DriverFailure]:
        """Detect if an event represents a driver failure."""
        message_lower = event.message.lower()

        for pattern in DRIVER_FAILURE_PATTERNS:
            if re.search(pattern, message_lower):
                failure_type = self._classify_failure(pattern, message_lower)
                driver_name = event.driver or self._extract_driver_from_message(event.message)

                if driver_name:
                    return DriverFailure(
                        driver_name=driver_name,
                        failure_type=failure_type,
                        timestamp=event.timestamp,
                        message=event.message,
                        line_number=event.line_number,
                        retry_count=0
                    )

        return None

    def _classify_failure(self, pattern: str, message: str) -> str:
        """Classify the type of failure."""
        if "firmware" in pattern or "firmware" in message:
            return "firmware_missing"
        elif "timeout" in pattern or "timeout" in message:
            return "timeout"
        elif "initialize" in pattern or "probe" in pattern:
            return "initialization_failed"
        elif "load" in pattern:
            return "load_failed"
        elif "device" in pattern:
            return "device_not_ready"
        else:
            return "unknown_failure"

    def _extract_driver_from_message(self, message: str) -> Optional[str]:
        """Extract driver name from message if not directly available."""
        match = re.search(r"(\w+_\w+|\w+driver):\s+", message)
        if match:
            return match.group(1)

        match = re.search(r"\[(\w+_\w+|\w+driver)\]", message)
        if match:
            return match.group(1)

        return None

    def get_failures(self) -> List[DriverFailure]:
        """Return all detected failures."""
        return self.failures

    def get_suspicious_drivers(self) -> Set[str]:
        """Return set of suspicious driver names."""
        return self.suspicious_drivers

    def get_failure_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of driver failures.

        Returns:
            Dictionary containing failure statistics
        """
        if not self.failures:
            return {
                "total_failures": 0,
                "failure_types": {},
                "affected_drivers": [],
                "most_common_failure": None
            }

        failure_types = {}
        for failure in self.failures:
            failure_types[failure.failure_type] = failure_types.get(failure.failure_type, 0) + 1

        driver_counts = {}
        for failure in self.failures:
            driver_counts[failure.driver_name] = driver_counts.get(failure.driver_name, 0) + 1

        most_common = max(failure_types.items(), key=lambda x: x[1])

        return {
            "total_failures": len(self.failures),
            "failure_types": failure_types,
            "affected_drivers": sorted(driver_counts.keys()),
            "driver_failure_counts": driver_counts,
            "most_common_failure": most_common[0],
            "most_common_failure_count": most_common[1]
        }

    def get_critical_failures(self) -> List[DriverFailure]:
        """
        Return critical failures (those with retries or firmware issues).

        Returns:
            List of critical DriverFailure objects
        """
        critical = []
        for failure in self.failures:
            if failure.retry_count >= 3:
                critical.append(failure)
            elif failure.failure_type == "firmware_missing":
                critical.append(failure)
            elif failure.failure_type == "timeout":
                critical.append(failure)

        return critical

    def get_failure_timeline(self) -> List[Dict[str, Any]]:
        """
        Get failures ordered by timestamp.

        Returns:
            List of failure dictionaries with timing info
        """
        failures_with_time = [f for f in self.failures if f.timestamp is not None]
        failures_with_time.sort(key=lambda x: x.timestamp)

        return [
            {
                "driver": f.driver_name,
                "type": f.failure_type,
                "timestamp": f.timestamp,
                "message": f.message,
                "retries": f.retry_count
            }
            for f in failures_with_time
        ]

    def generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on failure analysis.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        summary = self.get_failure_summary()

        if summary["total_failures"] == 0:
            recommendations.append("No driver failures detected. System appears stable.")
            return recommendations

        if "firmware_missing" in summary["failure_types"]:
            recommendations.append(
                f"Firmware files are missing for {summary['failure_types']['firmware_missing']} driver(s). "
                "Check firmware installation paths and ensure proprietary firmware is present."
            )

        if "timeout" in summary["failure_types"]:
            recommendations.append(
                f"Timeout errors detected ({summary['failure_types']['timeout']} occurrences). "
                "This may indicate hardware issues or driver communication problems."
            )

        if "initialization_failed" in summary["failure_types"]:
            recommendations.append(
                f"Driver initialization failures detected. "
                "Check device compatibility and driver version."
            )

        for driver, count in summary.get("driver_failure_counts", {}).items():
            if count >= 3:
                recommendations.append(
                    f"Driver '{driver}' failed {count} times. "
                    "Consider replacing hardware or updating driver."
                )

        return recommendations

"""
Driver failure analyzer module for detecting initialization failures, firmware issues, and retry patterns.
"""
