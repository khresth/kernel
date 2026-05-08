"""
Gradio dashboard UI for KernelScope.
"""

import gradio as gr
import pandas as pd
from typing import List, Optional, Tuple
from ..parsers import DmesgParser, LogcatParser, PanicParser
from ..parsers.base_parser import LogEvent
from ..visualizers import TimelineVisualizer, DependencyGraphVisualizer
from ..analyzers import DriverFailureAnalyzer, PanicDetector, LogComparator, DiagnosticSummary
from ..utils import detect_log_type


CUSTOM_CSS = """
/* Retro Linux Terminal Aesthetic (2008 era) */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

.gradio-container {
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    background: #000000 !important;
    color: #00ff66 !important;
    font-size: 12px !important;
}

.dark {
    --body-background-fill: #000000 !important;
    --background-fill-primary: #000000 !important;
    --background-fill-secondary: #000000 !important;
    --border-color-primary: #000000 !important;
    --border-color-accent: #00ff66 !important;
    --text-primary: #00ff66 !important;
    --text-secondary: #00ff66 !important;
    --body-text-color: #00ff66 !important;
}

.terminal-header {
    background: #000000 !important;
    border: 1px solid #000000 !important;
    border-bottom: 1px solid #00ff66 !important;
    padding: 8px 12px !important;
    margin: -20px -20px 16px -20px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    color: #00ff66 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

.terminal-panel {
    background: #000000 !important;
    border: 1px solid #000000 !important;
    border-radius: 0px !important;
    padding: 8px 12px !important;
    margin: 4px 0 !important;
}

.gr-button-primary {
    background: #000000 !important;
    border: 1px solid #00ff66 !important;
    color: #00ff66 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    padding: 6px 16px !important;
    border-radius: 0px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    box-shadow: none !important;
    transition: all 0.1s ease !important;
}

.gr-button-primary:hover {
    background: #00ff66 !important;
    color: #000000 !important;
    box-shadow: none !important;
}

.gr-button-secondary {
    background: #000000 !important;
    border: 1px solid #00ff66 !important;
    color: #00ff66 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
    font-size: 11px !important;
    padding: 6px 16px !important;
    border-radius: 0px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    box-shadow: none !important;
    transition: all 0.1s ease !important;
}

.gr-button-secondary:hover {
    background: #00ff66 !important;
    color: #000000 !important;
    box-shadow: none !important;
}

.tabs button {
    color: #00ff66 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid transparent !important;
    font-size: 11px !important;
    padding: 6px 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    transition: all 0.1s ease !important;
}

.tabs button:hover {
    color: #00ff66 !important;
    background: transparent !important;
}

.tabs button.selected {
    color: #00ff66 !important;
    background: transparent !important;
    border-bottom-color: #00ff66 !important;
}

.gr-textbox, .gr-dropdown {
    background: #000000 !important;
    border: 1px solid #00ff66 !important;
    color: #00ff66 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    border-radius: 0px !important;
    box-shadow: none !important;
    padding: 6px 8px !important;
}

.gr-textbox textarea, .gr-dropdown select {
    background: transparent !important;
    color: #00ff66 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}

.gr-textbox:focus-within, .gr-dropdown:focus-within {
    border-color: #00ff66 !important;
    box-shadow: none !important;
}

.gr-dataframe {
    background: #000000 !important;
    border: 1px solid #000000 !important;
    border-radius: 0px !important;
    box-shadow: none !important;
    overflow: hidden !important;
}

.gr-dataframe table {
    background: transparent !important;
    color: #00ff66 !important;
    border-collapse: collapse !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}

.gr-dataframe th {
    background: #000000 !important;
    color: #00ff66 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    font-weight: 600 !important;
    padding: 6px 8px !important;
    border-bottom: 1px solid #00ff66 !important;
}

.gr-dataframe td {
    color: #00ff66 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    padding: 4px 8px !important;
    border-bottom: 1px solid #00ff66 !important;
}

.gr-dataframe tr:hover td {
    background: #000000 !important;
}

.markdown {
    color: #00ff66 !important;
    font-family: 'JetBrains Mono', monospace !important;
    line-height: 1.4 !important;
    font-size: 11px !important;
}

.markdown h1, .markdown h2, .markdown h3 {
    color: #00ff66 !important;
    font-weight: 600 !important;
    margin-top: 12px !important;
    margin-bottom: 8px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    font-size: 12px !important;
}

.markdown code {
    background: #000000 !important;
    padding: 2px 6px !important;
    border-radius: 0px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    color: #ffcc00 !important;
}

.markdown strong {
    color: #ffcc00 !important;
}

.plot-container {
    background: #000000 !important;
    border: 1px solid #000000 !important;
    border-radius: 0px !important;
    box-shadow: none !important;
    padding: 8px !important;
}

.label {
    color: #00ff66 !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    font-weight: 600 !important;
    margin-bottom: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.terminal-footer {
    border-top: 1px solid #00ff66 !important;
    margin-top: 16px !important;
    padding: 8px 0 !important;
    display: flex !important;
    justify-content: space-between !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    color: #00ff66 !important;
    background: #000000 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

.blinking-cursor {
    animation: blink 1s step-end infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

.terminal-success {
    color: #00ff66 !important;
}

.terminal-warning {
    color: #ffcc00 !important;
}

.terminal-error {
    color: #ff4444 !important;
}

.terminal-muted {
    color: #00ff66 !important;
}

.gradio-container ::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

.gradio-container ::-webkit-scrollbar-track {
    background: #000000;
    border: 1px solid #00ff66;
}

.gradio-container ::-webkit-scrollbar-thumb {
    background: #00ff66;
    border: 1px solid #00ff66;
}

.gradio-container ::-webkit-scrollbar-thumb:hover {
    background: #00ff66;
}

.gradio-container {
    padding: 12px !important;
}

.gr-box {
    border-radius: 0px !important;
    padding: 6px !important;
    background: #000000 !important;
    border: 1px solid #000000 !important;
}

.gr-form {
    gap: 6px !important;
}

.log-output {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    line-height: 1.3 !important;
    color: #00ff66 !important;
    white-space: pre-wrap !important;
    word-break: break-all !important;
}

.log-error {
    color: #ff4444 !important;
}

.log-warning {
    color: #ffcc00 !important;
}

.log-timestamp {
    color: #00ff66 !important;
}
"""


class KernelScopeUI:
    """Main UI class for KernelScope dashboard."""

    def __init__(self):
        """Initialize the UI."""
        self.current_events: List[LogEvent] = []
        self.current_log_type: str = ""
        self.comparison_events: Optional[List[LogEvent]] = None

    def parse_log(self, file_path: str) -> Tuple[str, str, str, gr.Plot, gr.Plot]:
        """
        Parse uploaded log file and auto-generate charts.

        Args:
            file_path: Path to uploaded file

        Returns:
            Tuple of (status message, log type, preview, gantt_plot, dist_plot)
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            log_type = detect_log_type(content)

            if log_type == "dmesg":
                parser = DmesgParser()
            elif log_type == "logcat":
                parser = LogcatParser()
            elif log_type == "kernel_panic":
                parser = PanicParser()
            else:
                parser = DmesgParser()
                log_type = "dmesg (detected)"

            self.current_events = parser.parse(content)
            self.current_log_type = log_type

            preview_lines = content.split("\n")[:20]
            preview = "\n".join(preview_lines)

            status = f"Parsed {len(self.current_events)} events as {log_type}"

            visualizer = TimelineVisualizer(self.current_events)
            gantt_chart = visualizer.create_gantt_chart()
            dist_chart = visualizer.create_level_distribution()

            return status, log_type, preview, gantt_chart, dist_chart

        except Exception as e:
            return f"Error parsing file: {str(e)}", "unknown", "", None, None

    def generate_diagnostic_summary(self) -> str:
        """Generate diagnostic summary."""
        if not self.current_events:
            return "No log loaded. Please upload a log file first."

        summary_gen = DiagnosticSummary(self.current_events)
        return summary_gen.generate_summary()

    def get_driver_failures(self) -> pd.DataFrame:
        """Get driver failures as DataFrame."""
        if not self.current_events:
            return pd.DataFrame()

        analyzer = DriverFailureAnalyzer(self.current_events)
        failures = analyzer.get_failures()

        if not failures:
            return pd.DataFrame([{"message": "No driver failures detected"}])

        data = [
            {
                "Driver": f.driver_name,
                "Type": f.failure_type,
                "Time": f"{f.timestamp:.3f}s" if f.timestamp else "N/A",
                "Retries": f.retry_count,
                "Message": f.message[:80]
            }
            for f in failures
        ]
        return pd.DataFrame(data)

    def get_panic_info(self) -> str:
        """Get panic information."""
        if not self.current_events:
            return "No log loaded."

        detector = PanicDetector(self.current_events)
        return detector.get_human_readable_summary()

    def create_timeline(self, filter_level: str = "all") -> gr.Plot:
        """Create timeline visualization."""
        if not self.current_events:
            return None

        visualizer = TimelineVisualizer(self.current_events)
        if filter_level != "all":
            visualizer.filter_by_level(filter_level)

        return visualizer.create_timeline()

    def create_gantt_chart(self) -> gr.Plot:
        """Create Gantt chart."""
        if not self.current_events:
            return None

        visualizer = TimelineVisualizer(self.current_events)
        return visualizer.create_gantt_chart()

    def create_level_distribution(self) -> gr.Plot:
        """Create level distribution chart."""
        if not self.current_events:
            return None

        visualizer = TimelineVisualizer(self.current_events)
        return visualizer.create_level_distribution()

    def create_dependency_graph(self, layout: str = "spring") -> gr.Plot:
        """Create dependency graph."""
        if not self.current_events:
            return None

        visualizer = DependencyGraphVisualizer(self.current_events)
        return visualizer.create_plotly_graph(layout)

    def get_event_table(self, search_query: str = "") -> pd.DataFrame:
        """Get events as searchable table."""
        if not self.current_events:
            return pd.DataFrame()

        events = self.current_events
        if search_query:
            events = [e for e in events if search_query.lower() in e.message.lower()]

        data = [
            {
                "Time": f"{e.timestamp:.3f}s" if e.timestamp else "N/A",
                "Level": e.level,
                "Subsystem": e.subsystem,
                "Driver": e.driver or "N/A",
                "Message": e.message[:100]
            }
            for e in events[:500]  # Limit to 500 for performance
        ]
        return pd.DataFrame(data)

    def compare_logs(self, file_path: str) -> str:
        """Compare with another log file."""
        if not self.current_events:
            return "Please load a primary log first."

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            log_type = detect_log_type(content)
            if log_type == "dmesg":
                parser = DmesgParser()
            elif log_type == "logcat":
                parser = LogcatParser()
            else:
                parser = DmesgParser()

            comparison_events = parser.parse(content)

            comparator = LogComparator(
                self.current_events,
                comparison_events,
                label_a="Primary Log",
                label_b="Comparison Log"
            )

            return comparator.get_human_readable_summary()

        except Exception as e:
            return f"Error during comparison: {str(e)}"

    def export_report(self, format: str = "markdown") -> str:
        """Export diagnostic report."""
        if not self.current_events:
            return "No log loaded."

        summary_gen = DiagnosticSummary(self.current_events)
        report = summary_gen.generate_detailed_report()

        if format == "json":
            import json
            return json.dumps(report, indent=2)
        elif format == "markdown":
            return self._format_markdown_report(report)
        else:
            return str(report)

    def _format_markdown_report(self, report: dict) -> str:
        """Format report as markdown."""
        md = f"""# KernelScope Diagnostic Report

## Summary
{report['summary']}

## Severity Assessment
**Overall Severity:** {report['severity'].upper()}

## Panic Analysis
- Panics Detected: {report['panic_analysis']['panic_count']}
- Panic Types: {', '.join(report['panic_analysis']['panic_types'].keys())}

## Driver Analysis
- Total Failures: {report['driver_analysis']['total_failures']}
- Most Common Failure: {report['driver_analysis']['most_common_failure']}

## Event Statistics
- Total Events: {report['event_statistics']['total_events']}
- Error Events: {report['event_statistics']['level_distribution'].get('error', 0)}
- Warning Events: {report['event_statistics']['level_distribution'].get('warning', 0)}

## Recommendations
"""
        for rec in report['recommendations']:
            md += f"- {rec}\n"

        return md


def create_dashboard() -> gr.Blocks:
    """
    Create the main Gradio dashboard.

    Returns:
        Gradio Blocks app
    """
    ui = KernelScopeUI()

    with gr.Blocks(
        title="KernelScope",
        theme=gr.themes.Soft(),
        css=CUSTOM_CSS
    ) as app:
        gr.HTML("""
        <div class="terminal-header">
            KERNELSCOPE TERMINAL v4.2.1 | SESSION ACTIVE | HOST: LOCAL
        </div>
        """)

        with gr.Tabs():
            with gr.Tab("> INPUT"):
                with gr.Row():
                    log_input = gr.File(
                        label="",
                        file_types=[".txt", ".log"],
                        type="filepath"
                    )
                    parse_btn = gr.Button("[ EXECUTE INGEST ]", variant="primary")

                with gr.Row():
                    status_output = gr.Textbox(label="", interactive=False)
                    log_type_output = gr.Textbox(label="", interactive=False)

                log_preview = gr.Textbox(
                    label="",
                    lines=10,
                    interactive=False
                )

            with gr.Tab("> ANALYZE"):
                with gr.Row():
                    summary_btn = gr.Button("[ RUN DIAGNOSTICS ]", variant="primary")

                diagnostic_summary = gr.Markdown(label="")
                panic_info = gr.Textbox(label="", lines=10, interactive=False)

                with gr.Row():
                    level_filter = gr.Dropdown(
                        choices=["all", "error", "warning", "info"],
                        value="all",
                        label=""
                    )
                    timeline_btn = gr.Button("[ TIMELINE ]", variant="secondary")

                timeline_plot = gr.Plot(label="")

                with gr.Row():
                    gantt_btn = gr.Button("[ GANTT ]", variant="secondary")
                    dist_btn = gr.Button("[ DISTRIBUTION ]", variant="secondary")

                with gr.Row():
                    gantt_plot = gr.Plot(label="")
                    dist_plot = gr.Plot(label="")

            with gr.Tab("> DRIVERS"):
                driver_failures_table = gr.Dataframe(label="")
                refresh_drivers_btn = gr.Button("[ REFRESH ]", variant="secondary")

            with gr.Tab("> DEPENDENCIES"):
                with gr.Row():
                    layout_choice = gr.Dropdown(
                        choices=["spring", "circular", "kamada_kawai", "random"],
                        value="spring",
                        label=""
                    )
                    graph_btn = gr.Button("[ RENDER ]", variant="secondary")

                dependency_plot = gr.Plot(label="")

            with gr.Tab("> EVENTS"):
                search_box = gr.Textbox(label="", placeholder="> grep pattern...")
                search_btn = gr.Button("[ SEARCH ]", variant="secondary")
                event_table = gr.Dataframe(label="")

            with gr.Tab("> COMPARE"):
                with gr.Row():
                    comparison_input = gr.File(
                        label="",
                        file_types=[".txt", ".log"],
                        type="filepath"
                    )
                    compare_btn = gr.Button("[ DIFF ]", variant="primary")

                comparison_result = gr.Textbox(
                    label="",
                    lines=15,
                    interactive=False
                )

            with gr.Tab("> EXPORT"):
                with gr.Row():
                    export_format = gr.Dropdown(
                        choices=["markdown", "json"],
                        value="markdown",
                        label=""
                    )
                    export_btn = gr.Button("[ GENERATE REPORT ]", variant="primary")

                export_output = gr.Textbox(
                    label="",
                    lines=20,
                    interactive=False
                )

        gr.HTML("""
        <div class="terminal-footer">
            <span>kernelscope diagnostics v4.2.1</span>
            <span>build: 4.2.1+gita91f | arch: x86_64 | mode: production</span>
        </div>
        """)

        parse_btn.click(
            fn=ui.parse_log,
            inputs=[log_input],
            outputs=[status_output, log_type_output, log_preview, gantt_plot, dist_plot]
        )

        summary_btn.click(
            fn=ui.generate_diagnostic_summary,
            outputs=[diagnostic_summary]
        )

        timeline_btn.click(
            fn=ui.create_timeline,
            inputs=[level_filter],
            outputs=[timeline_plot]
        )

        gantt_btn.click(
            fn=ui.create_gantt_chart,
            outputs=[gantt_plot]
        )

        dist_btn.click(
            fn=ui.create_level_distribution,
            outputs=[dist_plot]
        )

        graph_btn.click(
            fn=ui.create_dependency_graph,
            inputs=[layout_choice],
            outputs=[dependency_plot]
        )

        refresh_drivers_btn.click(
            fn=ui.get_driver_failures,
            outputs=[driver_failures_table]
        )

        search_btn.click(
            fn=ui.get_event_table,
            inputs=[search_box],
            outputs=[event_table]
        )

        compare_btn.click(
            fn=ui.compare_logs,
            inputs=[comparison_input],
            outputs=[comparison_result]
        )

        export_btn.click(
            fn=ui.export_report,
            inputs=[export_format],
            outputs=[export_output]
        )

        def update_panic_info(status, log_type, preview):
            if "✅" in status:
                return ui.get_panic_info()
            return "No log loaded."

        parse_btn.click(
            fn=update_panic_info,
            inputs=[status_output, log_type_output, log_preview],
            outputs=[panic_info]
        )

        def update_driver_table(status, log_type, preview):
            if "✅" in status:
                return ui.get_driver_failures()
            return pd.DataFrame([{"message": "No log loaded"}])

        parse_btn.click(
            fn=update_driver_table,
            inputs=[status_output, log_type_output, log_preview],
            outputs=[driver_failures_table]
        )

    return app

"""
Dashboard UI module providing the retro terminal-style Gradio interface for KernelScope.
"""
