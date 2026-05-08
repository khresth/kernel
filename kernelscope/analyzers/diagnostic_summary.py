"""
AI diagnostic summary generator using heuristics.
"""

from typing import List, Dict, Any
from ..parsers.base_parser import LogEvent
from .driver_analyzer import DriverFailureAnalyzer
from .panic_detector import PanicDetector


class DiagnosticSummary:
    """Generates diagnostic summaries using heuristic analysis."""

    def __init__(self, events: List[LogEvent]):
        """
        Initialize diagnostic summary generator.

        Args:
            events: List of parsed log events
        """
        self.events = events
        self.driver_analyzer = DriverFailureAnalyzer(events)
        self.panic_detector = PanicDetector(events)

    def generate_summary(self) -> str:
        """
        Generate a concise diagnostic summary.

        Returns:
            Human-readable summary string
        """
        summary_parts = []

        if self.panic_detector.has_panics():
            panic_summary = self._generate_panic_summary()
            summary_parts.append(panic_summary)

        driver_summary = self._generate_driver_summary()
        if driver_summary:
            summary_parts.append(driver_summary)

        error_summary = self._generate_error_summary()
        if error_summary:
            summary_parts.append(error_summary)

        boot_summary = self._generate_boot_summary()
        if boot_summary:
            summary_parts.append(boot_summary)

        if not summary_parts:
            return "No critical issues detected."

        return " ".join(summary_parts)

    def _generate_panic_summary(self) -> str:
        """Generate panic-related summary."""
        panics = self.panic_detector.get_panics()
        panic_types = self.panic_detector.get_panic_summary()["panic_types"]

        if not panics:
            return ""

        if len(panics) == 1:
            panic = panics[0]
            if panic.panic_type == "kernel_panic":
                return "KERNEL PANIC detected. System crashed during operation."
            elif panic.panic_type == "segfault":
                return "Segmentation fault detected. Memory access violation caused system failure."
            elif panic.panic_type == "soft_lockup":
                return "Soft lockup detected. CPU stuck in infinite loop."
            elif panic.panic_type == "hard_lockup":
                return "Hard lockup detected. CPU completely unresponsive."
            elif panic.panic_type == "watchdog_reset":
                return "Watchdog reset triggered. System recovered from hang."
            else:
                return f"{panic.panic_type.replace('_', ' ').title()} detected."
        else:
            return f"Multiple crashes detected ({len(panics)}): {', '.join(panic_types.keys())}."

    def _generate_driver_summary(self) -> str:
        """Generate driver-related summary."""
        failures = self.driver_analyzer.get_failures()
        summary = self.driver_analyzer.get_failure_summary()

        if not failures:
            return ""

        if summary["total_failures"] == 1:
            failure = failures[0]
            if failure.failure_type == "firmware_missing":
                return f"{failure.driver_name} failed due to missing firmware file."
            elif failure.failure_type == "timeout":
                return f"{failure.driver_name} initialization timed out."
            elif failure.failure_type == "initialization_failed":
                return f"{failure.driver_name} failed to initialize."
            else:
                return f"{failure.driver_name} encountered errors during boot."
        else:
            most_common = summary["most_common_failure"]
            if most_common == "firmware_missing":
                return f"Multiple drivers failed due to missing firmware ({summary['total_failures']} failures)."
            elif most_common == "timeout":
                return f"Multiple driver timeouts detected ({summary['total_failures']} failures)."
            elif most_common == "initialization_failed":
                return f"Multiple driver initialization failures ({summary['total_failures']} failures)."
            else:
                return f"{summary['total_failures']} driver failures detected during boot."

    def _generate_error_summary(self) -> str:
        """Generate general error summary."""
        error_events = [e for e in self.events if e.level == "error"]
        warning_events = [e for e in self.events if e.level == "warning"]

        if not error_events and not warning_events:
            return ""

        error_subsystems = {}
        for event in error_events:
            error_subsystems[event.subsystem] = error_subsystems.get(event.subsystem, 0) + 1

        if error_subsystems:
            top_subsystem = max(error_subsystems.items(), key=lambda x: x[1])
            if top_subsystem[1] > 5:
                return f"{top_subsystem[0]} subsystem reported {top_subsystem[1]} errors."
            else:
                return f"{len(error_events)} errors detected across {len(error_subsystems)} subsystems."

        if warning_events:
            return f"{len(warning_events)} warnings detected in system logs."

        return ""

    def _generate_boot_summary(self) -> str:
        """Generate boot-related summary."""
        timed_events = [e for e in self.events if e.timestamp is not None]

        if not timed_events:
            return ""

        start_time = min(e.timestamp for e in timed_events)
        end_time = max(e.timestamp for e in timed_events)
        duration = end_time - start_time

        if duration > 60:
            return f"Boot sequence took {duration:.1f}s, which is unusually slow."
        elif duration > 30:
            return f"Boot sequence took {duration:.1f}s."
        else:
            return ""

    def generate_detailed_report(self) -> Dict[str, Any]:
        """
        Generate a detailed diagnostic report.

        Returns:
            Dictionary containing detailed analysis
        """
        report = {
            "summary": self.generate_summary(),
            "panic_analysis": self.panic_detector.get_panic_summary(),
            "driver_analysis": self.driver_analyzer.get_failure_summary(),
            "event_statistics": self._get_event_statistics(),
            "recommendations": self._generate_recommendations(),
            "severity": self._assess_severity()
        }

        return report

    def _get_event_statistics(self) -> Dict[str, Any]:
        """Get event statistics."""
        total_events = len(self.events)
        level_counts = {}
        subsystem_counts = {}

        for event in self.events:
            level_counts[event.level] = level_counts.get(event.level, 0) + 1
            subsystem_counts[event.subsystem] = subsystem_counts.get(event.subsystem, 0) + 1

        return {
            "total_events": total_events,
            "level_distribution": level_counts,
            "subsystem_distribution": subsystem_counts
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        recommendations.extend(self.driver_analyzer.generate_recommendations())

        if self.panic_detector.has_panics():
            panics = self.panic_detector.get_panics()
            if len(panics) > 1:
                recommendations.append(
                    "Multiple panics detected. Check for hardware issues or driver conflicts."
                )
            else:
                panic = panics[0]
                if panic.panic_type in ["segfault", "gpf", "page_fault"]:
                    recommendations.append(
                        "Memory-related panic detected. Check RAM and memory configuration."
                    )
                elif panic.panic_type in ["soft_lockup", "hard_lockup"]:
                    recommendations.append(
                        "Lockup detected. Check for infinite loops or driver bugs."
                    )

        error_count = sum(1 for e in self.events if e.level == "error")
        if error_count > 50:
            recommendations.append(
                f"High error count ({error_count}). Review system configuration and hardware."
            )

        return recommendations[:10]

    def _assess_severity(self) -> str:
        """Assess overall system health severity."""
        if self.panic_detector.has_panics():
            critical_panics = self.panic_detector.get_critical_panics()
            if critical_panics:
                return "critical"
            return "high"

        failures = self.driver_analyzer.get_failures()
        if len(failures) > 10:
            return "high"
        elif len(failures) > 3:
            return "medium"

        error_count = sum(1 for e in self.events if e.level == "error")
        if error_count > 20:
            return "medium"

        return "low"

"""
Diagnostic summary module for heuristic-based analysis and recommendation generation.
"""
