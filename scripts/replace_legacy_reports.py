from pathlib import Path
target = Path(__file__).resolve().parents[1] / 'ml_lab/ui/reports.py'
target.write_text('''"""Report interface backed by real artifacts and direct PDF exports.

Compatibility entry points for the modular ML Lab UI.
"""
from ml_lab.report_ui import (
    render_report_config,
    render_report_export,
    render_report_generator_ui,
    render_report_history,
    render_report_preview,
)
''', encoding='utf-8')
