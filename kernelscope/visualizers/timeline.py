"""
Boot timeline visualization using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..parsers.base_parser import LogEvent
from ..config import TIMELINE_COLORS


class TimelineVisualizer:
    """Creates interactive boot timeline visualizations."""

    def __init__(self, events: List[LogEvent]):
        """
        Initialize timeline visualizer.

        Args:
            events: List of parsed log events
        """
        self.events = events
        self.filtered_events = events

    def filter_by_level(self, level: str) -> "TimelineVisualizer":
        """Filter events by error level."""
        self.filtered_events = [e for e in self.events if e.level == level]
        return self

    def filter_by_subsystem(self, subsystem: str) -> "TimelineVisualizer":
        """Filter events by subsystem."""
        self.filtered_events = [e for e in self.events if e.subsystem == subsystem]
        return self

    def filter_by_driver(self, driver: str) -> "TimelineVisualizer":
        """Filter events by driver."""
        self.filtered_events = [e for e in self.events if e.driver == driver]
        return self

    def reset_filters(self) -> "TimelineVisualizer":
        """Reset all filters."""
        self.filtered_events = self.events
        return self

    def create_timeline(self) -> go.Figure:
        """
        Create an interactive boot timeline.

        Returns:
            Plotly figure object
        """
        fig = go.Figure()

        subsystem_events = {}
        for event in self.filtered_events:
            if event.timestamp is not None:
                if event.subsystem not in subsystem_events:
                    subsystem_events[event.subsystem] = []
                subsystem_events[event.subsystem].append(event)

        for subsystem, events in sorted(subsystem_events.items()):
            timestamps = [e.timestamp for e in events]
            levels = [e.level for e in events]
            messages = [e.message for e in events]
            drivers = [e.driver or "N/A" for e in events]

            colors = [TIMELINE_COLORS.get(level, TIMELINE_COLORS["info"]) for level in levels]

            fig.add_trace(go.Scatter(
                x=timestamps,
                y=[subsystem] * len(timestamps),
                mode="markers",
                name=subsystem,
                marker=dict(
                    size=8,
                    color=colors,
                    line=dict(width=1, color="white")
                ),
                text=[f"<b>{subsystem}</b><br>Driver: {driver}<br>Time: {ts:.3f}s<br>Level: {level}<br>{msg[:100]}"
                      for driver, ts, level, msg in zip(drivers, timestamps, levels, messages)],
                hovertemplate="%{text}<extra></extra>",
                hoverlabel=dict(bgcolor="rgba(0,0,0,0.8)", font_color="white")
            ))

        fig.update_layout(
            title="Boot Timeline Visualization",
            xaxis_title="Time (seconds)",
            yaxis_title="Subsystem",
            hovermode="closest",
            template="plotly_dark",
            height=600,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )

        return fig

    def create_gantt_chart(self) -> go.Figure:
        """
        Create a Gantt-style chart showing boot stages.

        Returns:
            Plotly figure object
        """
        fig = go.Figure()

        events_with_time = [e for e in self.filtered_events if e.timestamp is not None]
        if not events_with_time:
            return fig

        events_with_time.sort(key=lambda x: x.timestamp)

        stages = self._identify_stages(events_with_time)

        for stage in stages:
            fig.add_trace(go.Scatter(
                x=[stage["start"], stage["end"]],
                y=[stage["name"], stage["name"]],
                mode="lines",
                line=dict(color=stage["color"], width=20),
                name=stage["name"],
                hovertemplate=f"<b>{stage['name']}</b><br>Start: {stage['start']:.3f}s<br>End: {stage['end']:.3f}s<br>Duration: {stage['duration']:.3f}s<extra></extra>"
            ))

        fig.update_layout(
            title="Boot Stage Gantt Chart",
            xaxis_title="Time (seconds)",
            yaxis_title="Boot Stage",
            template="plotly_dark",
            height=500,
            showlegend=False
        )

        return fig

    def create_level_distribution(self) -> go.Figure:
        """
        Create a pie chart showing error level distribution.

        Returns:
            Plotly figure object
        """
        level_counts = {}
        for event in self.filtered_events:
            level_counts[event.level] = level_counts.get(event.level, 0) + 1

        fig = go.Figure(data=[go.Pie(
            labels=list(level_counts.keys()),
            values=list(level_counts.values()),
            marker=dict(colors=[TIMELINE_COLORS.get(level, TIMELINE_COLORS["info"]) 
                              for level in level_counts.keys()]),
            textinfo="label+percent",
            hole=0.3
        )])

        fig.update_layout(
            title="Error Level Distribution",
            template="plotly_dark",
            height=400
        )

        return fig

    def create_subsystem_heatmap(self) -> go.Figure:
        """
        Create a heatmap showing event frequency by subsystem and level.

        Returns:
            Plotly figure object
        """
        subsystems = sorted(set(e.subsystem for e in self.filtered_events))
        levels = sorted(set(e.level for e in self.filtered_events))

        matrix = []
        for subsystem in subsystems:
            row = []
            for level in levels:
                count = sum(1 for e in self.filtered_events 
                           if e.subsystem == subsystem and e.level == level)
                row.append(count)
            matrix.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=levels,
            y=subsystems,
            colorscale="Viridis",
            colorbar=dict(title="Event Count")
        ))

        fig.update_layout(
            title="Subsystem vs Level Heatmap",
            xaxis_title="Error Level",
            yaxis_title="Subsystem",
            template="plotly_dark",
            height=500
        )

        return fig

    def create_driver_load_sequence(self) -> go.Figure:
        """
        Create a sequence diagram showing driver load order.

        Returns:
            Plotly figure object
        """
        driver_events = [e for e in self.filtered_events 
                        if e.driver and e.timestamp is not None]
        driver_events.sort(key=lambda x: x.timestamp)

        if not driver_events:
            fig = go.Figure()
            fig.update_layout(
                title="Driver Load Sequence",
                template="plotly_dark",
                annotations=[dict(text="No driver events found", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False)]
            )
            return fig

        drivers = sorted(set(e.driver for e in driver_events))
        driver_load_times = {}

        for driver in drivers:
            driver_loads = [e.timestamp for e in driver_events if e.driver == driver]
            if driver_loads:
                driver_load_times[driver] = min(driver_loads)

        sorted_drivers = sorted(driver_load_times.items(), key=lambda x: x[1])

        fig = go.Figure()

        for i, (driver, load_time) in enumerate(sorted_drivers[:20]):
            fig.add_trace(go.Scatter(
                x=[load_time],
                y=[i],
                mode="markers",
                name=driver,
                marker=dict(size=12, color=TIMELINE_COLORS["info"]),
                text=f"<b>{driver}</b><br>Load Time: {load_time:.3f}s",
                hovertemplate="%{text}<extra></extra>"
            ))

        fig.update_yaxes(
            ticktext=[d[0] for d in sorted_drivers[:20]],
            tickvals=list(range(len(sorted_drivers[:20])))
        )

        fig.update_layout(
            title="Driver Load Sequence",
            xaxis_title="Time (seconds)",
            yaxis_title="Driver",
            template="plotly_dark",
            height=600,
            showlegend=False
        )

        return fig

    def _identify_stages(self, events: List[LogEvent]) -> List[Dict[str, Any]]:
        """
        Identify boot stages from events.

        Args:
            events: Events with timestamps

        Returns:
            List of stage dictionaries
        """
        stages = []
        stage_keywords = {
            "Kernel Init": ["Linux version", "Booting the kernel"],
            "Hardware Detect": ["PCI:", "ACPI:", "BIOS-provided"],
            "Memory Setup": ["Memory policy", "Calibrating"],
            "CPU Init": ["CPU:", "Brought up"],
            "Network Init": ["NET:", "eth"],
            "Storage Init": ["EXT4-fs", "SCSI"],
            "Service Start": ["systemd", "Starting"],
        }

        for stage_name, keywords in stage_keywords.items():
            stage_events = []
            for event in events:
                if any(kw.lower() in event.message.lower() for kw in keywords):
                    stage_events.append(event)

            if stage_events:
                start = min(e.timestamp for e in stage_events)
                end = max(e.timestamp for e in stage_events)
                stages.append({
                    "name": stage_name,
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "color": TIMELINE_COLORS["info"]
                })

        error_events = [e for e in events if e.level == "error"]
        if error_events:
            start = min(e.timestamp for e in error_events)
            end = max(e.timestamp for e in error_events)
            stages.append({
                "name": "Errors",
                "start": start,
                "end": end,
                "duration": end - start,
                "color": TIMELINE_COLORS["error"]
            })

        return sorted(stages, key=lambda x: x["start"])

"""
Timeline visualizer module for creating interactive boot timelines, Gantt charts, and distribution visualizations.
"""
