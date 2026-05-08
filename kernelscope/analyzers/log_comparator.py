"""
Log comparison engine for comparing two log files.
"""

from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from ..parsers.base_parser import LogEvent


@dataclass
class LogDifference:
    """Represents a difference between two logs."""
    diff_type: str  # 'missing_module', 'timing_change', 'new_error', 'regression'
    module: str
    details: str
    severity: str


class LogComparator:
    """Compares two logs to identify differences and regressions."""

    def __init__(self, events_a: List[LogEvent], events_b: List[LogEvent],
                 label_a: str = "Log A", label_b: str = "Log B"):
        """
        Initialize log comparator.

        Args:
            events_a: Events from first log
            events_b: Events from second log
            label_a: Label for first log
            label_b: Label for second log
        """
        self.events_a = events_a
        self.events_b = events_b
        self.label_a = label_a
        self.label_b = label_b
        self.differences: List[LogDifference] = []
        self._compare()

    def _compare(self) -> None:
        """Perform log comparison."""
        self._compare_modules()
        self._compare_errors()
        self._compare_timings()
        self._compare_boot_sequence()

    def _compare_modules(self) -> None:
        """Compare modules/drivers between logs."""
        modules_a = set(e.driver for e in self.events_a if e.driver)
        modules_b = set(e.driver for e in self.events_b if e.driver)

        missing_in_b = modules_a - modules_b
        for module in missing_in_b:
            self.differences.append(LogDifference(
                diff_type="missing_module",
                module=module,
                details=f"Module '{module}' present in {self.label_a} but missing in {self.label_b}",
                severity="warning"
            ))

        new_in_b = modules_b - modules_a
        for module in new_in_b:
            self.differences.append(LogDifference(
                diff_type="new_module",
                module=module,
                details=f"Module '{module}' present in {self.label_b} but not in {self.label_a}",
                severity="info"
            ))

    def _compare_errors(self) -> None:
        """Compare error counts between logs."""
        errors_a = [e for e in self.events_a if e.level == "error"]
        errors_b = [e for e in self.events_b if e.level == "error"]

        error_count_a = len(errors_a)
        error_count_b = len(errors_b)

        if error_count_b > error_count_a:
            self.differences.append(LogDifference(
                diff_type="new_error",
                module="system",
                details=f"Error count increased from {error_count_a} to {error_count_b}",
                severity="error"
            ))

        error_drivers_a = set(e.driver for e in errors_a if e.driver)
        error_drivers_b = set(e.driver for e in errors_b if e.driver)

        new_error_drivers = error_drivers_b - error_drivers_a
        for driver in new_error_drivers:
            self.differences.append(LogDifference(
                diff_type="new_error",
                module=driver,
                details=f"New errors from driver '{driver}' in {self.label_b}",
                severity="error"
            ))

    def _compare_timings(self) -> None:
        """Compare timing of key events."""
        timed_a = {e.driver: e.timestamp for e in self.events_a 
                   if e.driver and e.timestamp is not None}
        timed_b = {e.driver: e.timestamp for e in self.events_b 
                   if e.driver and e.timestamp is not None}

        common_drivers = set(timed_a.keys()) & set(timed_b.keys())

        for driver in common_drivers:
            time_a = timed_a[driver]
            time_b = timed_b[driver]
            diff = time_b - time_a

            if abs(diff) > 1.0:
                severity = "warning" if abs(diff) < 5.0 else "error"
                change = "slower" if diff > 0 else "faster"
                self.differences.append(LogDifference(
                    diff_type="timing_change",
                    module=driver,
                    details=f"'{driver}' initialization {change} by {abs(diff):.2f}s "
                           f"({self.label_a}: {time_a:.2f}s -> {self.label_b}: {time_b:.2f}s)",
                    severity=severity
                ))

    def _compare_boot_sequence(self) -> None:
        """Compare boot sequence order."""
        boot_a = [e for e in self.events_a if e.timestamp is not None][:50]
        boot_b = [e for e in self.events_b if e.timestamp is not None][:50]

        if not boot_a or not boot_b:
            return

        subsystems_a = [e.subsystem for e in boot_a]
        subsystems_b = [e.subsystem for e in boot_b]

        for i, (sub_a, sub_b) in enumerate(zip(subsystems_a, subsystems_b)):
            if sub_a != sub_b:
                self.differences.append(LogDifference(
                    diff_type="sequence_change",
                    module=sub_b,
                    details=f"Boot sequence changed at position {i}: "
                           f"{self.label_a} had '{sub_a}', {self.label_b} has '{sub_b}'",
                    severity="warning"
                ))
                break

        total_time_a = boot_a[-1].timestamp - boot_a[0].timestamp if len(boot_a) > 1 else 0
        total_time_b = boot_b[-1].timestamp - boot_b[0].timestamp if len(boot_b) > 1 else 0

        if abs(total_time_b - total_time_a) > 2.0:
            change = "slower" if total_time_b > total_time_a else "faster"
            severity = "warning" if abs(total_time_b - total_time_a) < 10.0 else "error"
            self.differences.append(LogDifference(
                diff_type="timing_change",
                module="boot",
                details=f"Boot time {change}: {self.label_a} ({total_time_a:.2f}s) -> "
                       f"{self.label_b} ({total_time_b:.2f}s)",
                severity=severity
            ))

    def get_differences(self) -> List[LogDifference]:
        """Return all detected differences."""
        return self.differences

    def get_differences_by_type(self, diff_type: str) -> List[LogDifference]:
        """Filter differences by type."""
        return [d for d in self.differences if d.diff_type == diff_type]

    def get_differences_by_severity(self, severity: str) -> List[LogDifference]:
        """Filter differences by severity."""
        return [d for d in self.differences if d.severity == severity]

    def has_regressions(self) -> bool:
        """Check if there are any regressions (new errors or significant slowdowns)."""
        for diff in self.differences:
            if diff.severity == "error" or diff.diff_type == "new_error":
                return True
        return False

    def get_comparison_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the comparison.

        Returns:
            Dictionary containing comparison statistics
        """
        diff_types = {}
        severity_counts = {}

        for diff in self.differences:
            diff_types[diff.diff_type] = diff_types.get(diff.diff_type, 0) + 1
            severity_counts[diff.severity] = severity_counts.get(diff.severity, 0) + 1

        return {
            "total_differences": len(self.differences),
            "difference_types": diff_types,
            "severity_counts": severity_counts,
            "has_regressions": self.has_regressions(),
            "label_a": self.label_a,
            "label_b": self.label_b
        }

    def get_human_readable_summary(self) -> str:
        """
        Generate a human-readable comparison summary.

        Returns:
            Formatted summary string
        """
        if not self.differences:
            return f"No significant differences between {self.label_a} and {self.label_b}."

        summary = f"COMPARISON: {self.label_a} vs {self.label_b}\n"
        summary += f"Found {len(self.differences)} difference(s):\n\n"

        # Group by severity
        errors = [d for d in self.differences if d.severity == "error"]
        warnings = [d for d in self.differences if d.severity == "warning"]
        info = [d for d in self.differences if d.severity == "info"]

        if errors:
            summary += f"ERRORS ({len(errors)}):\n"
            for diff in errors[:5]:  # Limit to 5
                summary += f"  - {diff.details}\n"
            if len(errors) > 5:
                summary += f"  ... and {len(errors) - 5} more\n"
            summary += "\n"

        if warnings:
            summary += f"WARNINGS ({len(warnings)}):\n"
            for diff in warnings[:5]:
                summary += f"  - {diff.details}\n"
            if len(warnings) > 5:
                summary += f"  ... and {len(warnings) - 5} more\n"
            summary += "\n"

        if info:
            summary += f"INFO ({len(info)}):\n"
            for diff in info[:3]:
                summary += f"  - {diff.details}\n"
            if len(info) > 3:
                summary += f"  ... and {len(info) - 3} more\n"

        if self.has_regressions():
            summary += "\nREGRESSIONS DETECTED - Review recommended\n"

        return summary

"""
Log comparator module for comparing two logs to identify differences, regressions, and timing changes.
"""
