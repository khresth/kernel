"""
Kernel panic detector for identifying crashes and fatal errors.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..parsers.base_parser import LogEvent
from ..config import PANIC_PATTERNS


@dataclass
class PanicInfo:
    """Represents a kernel panic or crash event."""
    panic_type: str
    timestamp: Optional[float]
    crash_address: Optional[str]
    stack_trace: List[str]
    registers: Dict[str, str]
    message: str
    line_number: int


class PanicDetector:
    """Detects and analyzes kernel panics and crashes."""

    def __init__(self, events: List[LogEvent]):
        """
        Initialize panic detector.

        Args:
            events: List of parsed log events
        """
        self.events = events
        self.panics: List[PanicInfo] = []
        self.crash_signatures: List[str] = []
        self._detect_panics()

    def _detect_panics(self) -> None:
        """Detect kernel panics and crashes from events."""
        in_panic_context = False
        current_panic = None

        for event in self.events:
            # Check for panic start
            panic_type = self._identify_panic_type(event.message)
            if panic_type:
                in_panic_context = True
                current_panic = PanicInfo(
                    panic_type=panic_type,
                    timestamp=event.timestamp,
                    crash_address=None,
                    stack_trace=[],
                    registers={},
                    message=event.message,
                    line_number=event.line_number
                )

            # Extract crash address
            if current_panic and not current_panic.crash_address:
                crash_addr = self._extract_crash_address(event.message)
                if crash_addr:
                    current_panic.crash_address = crash_addr

            # Collect stack trace
            if in_panic_context and self._is_stack_trace_line(event.message):
                if current_panic:
                    current_panic.stack_trace.append(event.message)

            # Extract registers
            if in_panic_context and self._is_register_line(event.message):
                if current_panic:
                    regs = self._extract_registers(event.message)
                    current_panic.registers.update(regs)

            # End panic context
            if in_panic_context and self._is_panic_end(event.message):
                if current_panic:
                    self.panics.append(current_panic)
                    self.crash_signatures.append(self._generate_signature(current_panic))
                in_panic_context = False
                current_panic = None

        # Add any remaining panic
        if current_panic:
            self.panics.append(current_panic)
            self.crash_signatures.append(self._generate_signature(current_panic))

    def _identify_panic_type(self, message: str) -> Optional[str]:
        """Identify the type of panic from message."""
        message_lower = message.lower()

        for pattern in PANIC_PATTERNS:
            if re.search(pattern, message_lower):
                if "soft lockup" in message_lower:
                    return "soft_lockup"
                elif "hard lockup" in message_lower:
                    return "hard_lockup"
                elif "segmentation fault" in message_lower:
                    return "segfault"
                elif "general protection" in message_lower:
                    return "gpf"
                elif "page fault" in message_lower:
                    return "page_fault"
                elif "double fault" in message_lower:
                    return "double_fault"
                elif "stack overflow" in message_lower:
                    return "stack_overflow"
                elif "watchdog" in message_lower:
                    return "watchdog_reset"
                elif "rcu" in message_lower:
                    return "rcu_stall"
                elif "kernel panic" in message_lower:
                    return "kernel_panic"

        return None

    def _extract_crash_address(self, message: str) -> Optional[str]:
        """Extract crash address from message."""
        match = re.search(r"RIP:\s+0033:\[<([0-9a-f]+)>\]|PC\s+is\s+at\s+([0-9a-f]+)", message, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2)
        return None

    def _is_stack_trace_line(self, message: str) -> bool:
        """Check if line is part of stack trace."""
        if re.search(r"Call\s+Trace:|Stack:", message, re.IGNORECASE):
            return True
        if re.search(r"\[<[0-9a-f]+>\]", message):
            return True
        if re.search(r"\w+\+0x[0-9a-f]+/0x[0-9a-f]+", message):
            return True
        return False

    def _is_register_line(self, message: str) -> bool:
        """Check if line contains register dump."""
        return bool(re.search(r"RAX:\s+[0-9a-f]+\s+RBX:", message, re.IGNORECASE))

    def _extract_registers(self, message: str) -> Dict[str, str]:
        """Extract register values from message."""
        registers = {}
        matches = re.findall(r"([A-Z]{3}):\s+([0-9a-f]+)", message, re.IGNORECASE)
        for reg, value in matches:
            registers[reg] = value
        return registers

    def _is_panic_end(self, message: str) -> bool:
        """Check if line indicates end of panic context."""
        if not message.strip():
            return True
        if "---" in message:
            return True
        return False

    def _generate_signature(self, panic: PanicInfo) -> str:
        """Generate a unique signature for the panic."""
        parts = [panic.panic_type]
        if panic.crash_address:
            parts.append(panic.crash_address)
        if panic.stack_trace:
            first_frame = panic.stack_trace[0] if panic.stack_trace else ""
            func_match = re.search(r"(\w+)\+0x", first_frame)
            if func_match:
                parts.append(func_match.group(1))
        return ":".join(parts)

    def get_panics(self) -> List[PanicInfo]:
        """Return all detected panics."""
        return self.panics

    def has_panics(self) -> bool:
        """Check if any panics were detected."""
        return len(self.panics) > 0

    def get_panic_count(self) -> int:
        """Return number of detected panics."""
        return len(self.panics)

    def get_crash_signatures(self) -> List[str]:
        """Return crash signatures."""
        return self.crash_signatures

    def get_panic_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of detected panics.

        Returns:
            Dictionary containing panic statistics
        """
        if not self.panics:
            return {
                "panic_count": 0,
                "panic_types": {},
                "has_panics": False
            }

        # Count by panic type
        panic_types = {}
        for panic in self.panics:
            panic_types[panic.panic_type] = panic_types.get(panic.panic_type, 0) + 1

        return {
            "panic_count": len(self.panics),
            "panic_types": panic_types,
            "has_panics": True,
            "crash_signatures": self.crash_signatures
        }

    def get_human_readable_summary(self) -> str:
        """
        Generate a human-readable summary of panics.

        Returns:
            Formatted summary string
        """
        if not self.panics:
            return "No kernel panics or crashes detected."

        summary = f"DETECTED {len(self.panics)} KERNEL PANIC(S)/CRASH(ES):\n\n"

        for i, panic in enumerate(self.panics, 1):
            summary += f"Panic #{i}:\n"
            summary += f"  Type: {panic.panic_type}\n"
            if panic.crash_address:
                summary += f"  Crash Address: 0x{panic.crash_address}\n"
            if panic.timestamp:
                summary += f"  Timestamp: {panic.timestamp:.3f}s\n"
            summary += f"  Message: {panic.message[:100]}...\n"
            if panic.stack_trace:
                summary += f"  Stack Depth: {len(panic.stack_trace)} frames\n"
            summary += "\n"

        return summary

    def get_critical_panics(self) -> List[PanicInfo]:
        """
        Return panics considered critical (non-watchdog related).

        Returns:
            List of critical PanicInfo objects
        """
        critical_types = {
            "kernel_panic", "segfault", "gpf", "page_fault", 
            "double_fault", "stack_overflow"
        }

        return [p for p in self.panics if p.panic_type in critical_types]

    def get_watchdog_events(self) -> List[PanicInfo]:
        """
        Return watchdog-related events.

        Returns:
            List of watchdog PanicInfo objects
        """
        watchdog_types = {"soft_lockup", "hard_lockup", "watchdog_reset", "rcu_stall"}
        return [p for p in self.panics if p.panic_type in watchdog_types]

"""
Panic detector module for identifying kernel panics, crashes, and extracting stack traces with register information.
"""
