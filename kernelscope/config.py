"""
Configuration settings for KernelScope.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class LogType:
    """Represents a log type with detection patterns."""
    name: str
    patterns: List[str]
    description: str


LOG_TYPES = {
    "dmesg": LogType(
        name="dmesg",
        patterns=[
            r"\[\s*\d+\.\d+\]",
            r"kernel:\s*\[",
            r"^\[\s*\d+\.\d+\]\s+\w+\s+\d+:\d+:\d+",
        ],
        description="Linux kernel ring buffer logs"
    ),
    "logcat": LogType(
        name="logcat",
        patterns=[
            r"\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3}",
            r"[VDIWEF]/",
            r"^\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+[VDIWEF]",
        ],
        description="Android logcat logs"
    ),
    "kernel_panic": LogType(
        name="kernel_panic",
        patterns=[
            r"kernel\s+panic",
            r"Kernel\s+panic",
            r"BUG:\s+soft\s+lockup",
            r"general\s+protection\s+fault",
            r"segmentation\s+fault",
            r"Call\s+Trace:",
            r"RIP:\s+0033:",
        ],
        description="Kernel panic and crash traces"
    ),
    "boot": LogType(
        name="boot",
        patterns=[
            r"Linux\s+version",
            r"Command\s+line:",
            r"Booting\s+the\s+kernel",
            r"ACPI:\s+Core",
            r"PCI:\s+Using",
        ],
        description="System boot sequence logs"
    ),
}


ERROR_LEVELS = {
    "EMERG": 0,
    "ALERT": 1,
    "CRIT": 2,
    "ERR": 3,
    "WARNING": 4,
    "NOTICE": 5,
    "INFO": 6,
    "DEBUG": 7,
}

LOGCAT_SEVERITY = {
    "V": "VERBOSE",
    "D": "DEBUG",
    "I": "INFO",
    "W": "WARNING",
    "E": "ERROR",
    "F": "FATAL",
}

KNOWN_SUBSYSTEMS = [
    "PCI", "ACPI", "USB", "Network", "GPU", "Audio", "Bluetooth",
    "WiFi", "Storage", "Memory", "CPU", "Thermal", "Power",
    "Display", "Camera", "Sensors", "Security", "Filesystem",
]

DRIVER_FAILURE_PATTERNS = [
    r"failed to initialize",
    r"initialization failed",
    r"probe failed",
    r"unable to load",
    r"load failed",
    r"firmware not found",
    r"firmware missing",
    r"timeout",
    r"device not ready",
    r"no such device",
    r"operation not permitted",
]

PANIC_PATTERNS = [
    r"kernel\s+panic\s+-?\s*not\s+syncing",
    r"BUG:\s+soft\s+lockup",
    r"BUG:\s+hard\s+lockup",
    r"general\s+protection\s+fault",
    r"segmentation\s+fault",
    r"page\s+fault",
    r"double\s+fault",
    r"stack\s+overflow",
    r"watchdog:\s+BUG",
    r"rcu_sched\s+self-detected\s+stall",
]

BOOT_EVENT_KEYWORDS = [
    "Booting the kernel",
    "Linux version",
    "Command line",
    "BIOS-provided physical RAM map",
    "Memory policy",
    "CPU:",
    "Calibrating delay",
    "Mount-cache hash table",
    "CPU0:",
    "Brought up",
    "NET:",
    "PCI:",
    "ACPI:",
    "Serial:",
    "USB",
    "EXT4-fs",
    " systemd",
    "Starting",
    "Reached target",
]

TIMELINE_COLORS = {
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6",
    "critical": "#8B5CF6",
}

REPORT_TEMPLATE_MD = """# KernelScope Diagnostic Report

**Generated:** {timestamp}
**Log Type:** {log_type}
**Log File:** {log_file}

## Executive Summary
{summary}

## Critical Issues
{critical_issues}

## Timeline Analysis
{timeline}

## Detailed Findings
{findings}

## Recommendations
{recommendations}
"""

"""
Configuration module for log type detection, error levels, and pattern matching.
"""
