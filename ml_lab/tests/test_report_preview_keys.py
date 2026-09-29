"""Rendering identical charts in current and historical previews must be safe."""
import runpy
import sys
import types
from pathlib import Path
from unittest.mock import patch


def test_identical_report_charts_have_unique_ids_across_previews():
    keys = []
    st = types.ModuleType('streamlit')
    for name in ['subheader', 'caption', 'markdown', 'write', 'dataframe']:
        setattr(st, name, lambda *args, **kwargs: None)
    def plotly_chart(fig, **kwargs):
        key = kwargs.get('key')
        assert key is not None
        assert key not in keys
        keys.append(key)
    st.plotly_chart = plotly_chart
    px = types.ModuleType('plotly.express')
    px.bar = lambda *args, **kwargs: {'same': 'figure'}
    plotly = types.ModuleType('plotly')
    plotly.__path__ = []
    plotly.express = px
    modules = {'streamlit': st, 'plotly': plotly, 'plotly.express': px}
    with patch.dict(sys.modules, modules):
        ui = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'report_ui.py'))
        report = {'metadata': {'title': 'Informe', 'author': '', 'generated_at': '2026-09-29T10:00:00+00:00'},
                  'options': {'include_charts': True, 'include_tables': True}, 'sections': [],
                  'charts': [{'kind': 'bar', 'labels': ['Modelo'], 'values': [0.5], 'title': 'R²', 'ylabel': 'R²'}] * 2}
        for location in ['current_generated_report', 'history_report_a', 'history_report_b']:
            ui['render_report_preview'](report, key_prefix=location)
    assert len(keys) == 6
