# KernelScope

A Linux and Android system diagnostics dashboard I built to analyze kernel logs, boot sequences, and crash traces when I couldn't find a good Windows-native solution.

I was working on embedded systems debugging and constantly needed to analyze Linux kernel logs, Android boot sequences, and crash traces. The problem was:

1. **I work on Windows** - Most kernel debugging tools are Linux-native and don't run on Windows without setting up VMs, Docker, or dual-booting
2. **Tool fragmentation** - I needed different tools for dmesg logs, logcat, kernel panics, and boot analysis
3. **Manual analysis was painful** - I spent time scrolling through logs, grepping for patterns, and manually correlating events
4. **No unified view** - I couldn't easily visualize boot timelines, driver dependencies, or compare logs side-by-side
5. **Hardware constraints** - I didn't always have access to boards, Raspberry Pi, or devices for testing

I tried various solutions but nothing gave me what I needed:
- SSH-ing into Linux machines (slow, network dependent)
- Running Docker on Windows (overhead, complexity)
- Manual grep/awk in WSL (tedious and also no visualizations)

---

I built a comprehensive diagnostics platform that runs entirely on Windows using Python. It simulates the tooling used by embedded systems engineers but without requiring Linux installation, Android hardware, Raspberry Pi devices, Docker, or virtual machines.

- **Multi-Log Support**: Parse dmesg, logcat, kernel panic, and boot logs automatically
- **Automated Analysis**: Detect driver failures, kernel panics, and boot regressions without manual grep
- **Interactive Visualizations**: Boot timelines, dependency graphs, and heatmaps for quick insights
- **Log Comparison**: Compare two logs to identify regressions between builds
- **AI Diagnostics**: Heuristic-based diagnostic summaries that tell me what's wrong
- **Export Reports**: Generate markdown, JSON, and HTML reports for documentation

---

## Screenshots






---

## Features

### Core Features

1. **Multi-Log Upload System**
   - Support for .txt and .log files
   - Automatic log type detection (dmesg, logcat, kernel panic, boot)
   - Batch upload support

2. **Log Parsing Engine**
   - Specialized parsers for dmesg, logcat, and kernel panic logs
   - Extract timestamps, subsystems, drivers, and error levels
   - Identify boot events and crash signatures

3. **Boot Timeline Visualization**
   - Interactive Plotly timelines
   - Initialization order visualization
   - Driver loading stages with hover tooltips
   - Filtering by level, subsystem, or driver

4. **Driver Failure Analyzer**
   - Detect failed driver initialization
   - Identify firmware missing errors
   - Track dependency failures and retries
   - Highlight timeout events and suspicious modules

5. **Kernel Panic Detector**
   - Identify kernel panics and segmentation faults
   - Extract stack traces and crash signatures
   - Detect watchdog resets and thermal shutdowns
   - Generate human-readable summaries

6. **Log Comparison Engine**
   - Compare two uploaded logs
   - Highlight missing modules and changed timings
   - Detect new errors and boot regressions
   - Side-by-side diff analysis

7. **AI Diagnostic Summary**
   - Concise summaries like "GPU initialization failed after firmware timeout"
   - Heuristic-based analysis (no API key required)
   - Severity assessment and recommendations

8. **Dependency Graph Visualization**
   - Module relationship graphs using networkx
   - Initialization chain visualization
   - Subsystem dependency mapping
   - Multiple layout options (spring, circular, kamada-kawai)

9. **Dashboard UI**
   - Gradio-based dark theme interface
   - Upload panels and analysis tabs
   - Interactive charts and searchable tables
   - Error summaries and comparison views

10. **Engineering-Focused UX**
    - Terminal-style formatting
    - Technical terminology
    - Structured diagnostics
    - Expandable trace sections

11. **Reporting**
    - Markdown reports
    - JSON diagnostics
    - HTML summaries with styling

---

1. **Upload a Log File**
   - Navigate to the "Upload & Parse" tab
   - Select a .txt or .log file
   - Click "Parse Log"
   - The system will automatically detect the log type

2. **Generate Diagnostic Summary**
   - Go to the "Analysis" tab
   - Click "Generate Diagnostic Summary"
   - Review the AI-generated summary

3. **Visualize Boot Timeline**
   - In the "Analysis" tab, select a filter level
   - Click "Generate Timeline"
   - Interact with the visualization using hover tooltips

4. **Analyze Driver Failures**
   - Navigate to the "Driver Analysis" tab
   - Review the driver failures table
   - Check for firmware issues and timeouts

5. **View Dependency Graph**
   - Go to the "Dependency Graph" tab
   - Select a layout algorithm
   - Click "Generate Graph"
   - Explore module relationships

6. **Compare Logs**
   - Load a primary log first
   - Go to the "Log Comparison" tab
   - Upload a comparison log
   - Click "Compare Logs"
   - Review differences and regressions

7. **Export Report**
   - Go to the "Export Report" tab
   - Select format (markdown, JSON, or HTML)
   - Click "Export"
   - Save the report

### My Logs

Only for testing
- `linux_boot.log` - Normal Linux boot sequence
- `android_boot.log` - Android boot with system services
- `kernel_panic.log` - Kernel panic with stack trace
- `gpu_failure.log` - GPU firmware failure
- `thermal_throttling.log` - Thermal shutdown scenario

---


### Project Structure

```
kernelscope/
├── kernelscope/
│   ├── __init__.py
│   ├── config.py              # Configuration and constants
│   ├── utils.py               # Utility functions
│   ├── parsers/               # Log parsing modules
│   │   ├── __init__.py
│   │   ├── base_parser.py     # Base parser class
│   │   ├── dmesg_parser.py    # dmesg log parser
│   │   ├── logcat_parser.py   # Android logcat parser
│   │   └── panic_parser.py    # Kernel panic parser
│   ├── analyzers/             # Analysis modules
│   │   ├── __init__.py
│   │   ├── driver_analyzer.py # Driver failure analysis
│   │   ├── panic_detector.py  # Panic detection
│   │   ├── log_comparator.py  # Log comparison
│   │   └── diagnostic_summary.py # AI summary generation
│   ├── visualizers/           # Visualization modules
│   │   ├── __init__.py
│   │   ├── timeline.py        # Boot timeline visualization
│   │   └── dependency_graph.py # Dependency graph visualization
│   ├── ui/                    # User interface
│   │   ├── __init__.py
│   │   └── dashboard.py       # Gradio dashboard
│   └── reporting.py           # Report generation
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Module Descriptions

#### Parsers
- **BaseParser**: Abstract base class defining the parser interface
- **DmesgParser**: Parses Linux kernel ring buffer logs with timestamp extraction
- **LogcatParser**: Parses Android logcat logs with severity level detection
- **PanicParser**: Specialized parser for kernel panic and crash traces

#### Analyzers
- **DriverFailureAnalyzer**: Detects driver initialization failures and retry patterns
- **PanicDetector**: Identifies kernel panics, stack traces, and crash signatures
- **LogComparator**: Compares two logs to identify regressions and differences
- **DiagnosticSummary**: Generates AI-style diagnostic summaries using heuristics

#### Visualizers
- **TimelineVisualizer**: Creates interactive boot timelines with Plotly
- **DependencyGraphVisualizer**: Builds module dependency graphs with networkx

#### UI
- **Dashboard**: Gradio-based web interface with dark theme and tabbed navigation

### Design Principles

- **Modularity**: Each component is independent and reusable
- **Type Hints**: Full type annotations for better code quality
- **Documentation**: Comprehensive docstrings for all public APIs
- **Error Handling**: Robust error handling with informative messages
- **Performance**: Efficient parsing and visualization for large logs

---
