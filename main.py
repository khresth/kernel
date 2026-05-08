"""
Main entry point for KernelScope application.
"""

import sys
from kernelscope.ui import create_dashboard


def main():
    """Launch the KernelScope Gradio dashboard."""
    print("Starting KernelScope...")
    print("-" * 40)

    app = create_dashboard()

    print("Dashboard initialized")
    print("Launching web interface on http://127.0.0.1:7860")
    print("-" * 40)

    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False,
        inbrowser=True
    )


if __name__ == "__main__":
    main()

"""
Main entry point for launching the KernelScope Gradio dashboard on localhost:7860.
"""
