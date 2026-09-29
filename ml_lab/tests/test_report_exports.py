import json
import tempfile
from pathlib import Path
from ml_lab.report_exports import build_report, export_report


def fixture_report(root, charts=True, template='technical'):
    folder = Path(root) / 'ml_lab/artifacts'
    folder.mkdir(parents=True, exist_ok=True)
    result = {'created_at': '2026-09-29', 'protocol': 'chronological_train_validation_test',
        'winner': 'Ridge', 'partitions': {'train': {'years': [2000, 2001]}, 'test': {'years': [2002]}},
        'results': [{'model': 'Ridge', 'validation_r2': 0.12, 'test_r2': -0.27,
                     'test_rmse_kg_ha': 432.1, 'test_mae_kg_ha': 300.2}]}
    (folder / 'common_benchmark.json').write_text(json.dumps(result), encoding='utf-8')
    return build_report(root, template=template, include_charts=charts, title='Informe de prueba', author='Equipo')


def test_exports_use_recorded_metrics_and_generate_real_pdf():
    import io
    from pypdf import PdfReader
    with tempfile.TemporaryDirectory() as root:
        report = fixture_report(root)
        assert report['sections'][1]['rows'][0][3] == 432.1
        pdf = export_report(report, 'pdf')
        assert pdf.startswith(b'%PDF-')
        assert '432.1' in ''.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
        assert b'<svg' in export_report(report, 'html')
        assert b'data:image/svg+xml' in export_report(report, 'markdown')


def test_include_charts_option_is_respected():
    with tempfile.TemporaryDirectory() as root:
        report = fixture_report(root, charts=False)
        assert not report['charts']
        assert b'<svg' not in export_report(report, 'html')
        assert b'data:image' not in export_report(report, 'markdown')


def test_templates_and_missing_artifacts_are_explicit():
    with tempfile.TemporaryDirectory() as root:
        executive = fixture_report(root, charts=False, template='executive')
        audit = fixture_report(root, charts=False, template='audit')
        assert 'raw_records' not in executive
        assert 'common_benchmark.json' in audit['raw_records']
        assert any(s['title'] == 'Trazabilidad de fuentes' for s in audit['sections'])
        assert 'statistical_analysis.json' in audit['unavailable']


def test_html_escapes_user_content_and_tables_can_be_disabled():
    with tempfile.TemporaryDirectory() as root:
        report = fixture_report(root, charts=False)
        report['metadata']['title'] = '<script>alert(1)</script>'
        report['options']['include_tables'] = False
        output = export_report(report, 'html')
        assert b'<script>' not in output
        assert b'&lt;script&gt;' in output
        assert b'<table>' not in output


def test_all_formats_work_when_reportlab_is_missing():
    import builtins
    import io
    from pypdf import PdfReader
    original_import = builtins.__import__
    def without_reportlab(name, *args, **kwargs):
        if name.startswith('reportlab'):
            raise ModuleNotFoundError("No module named 'reportlab'", name='reportlab')
        return original_import(name, *args, **kwargs)
    with tempfile.TemporaryDirectory() as root:
        report = fixture_report(root)
        try:
            builtins.__import__ = without_reportlab
            outputs = {kind: export_report(report, kind) for kind in ['markdown', 'html', 'json', 'pdf']}
        finally:
            builtins.__import__ = original_import
        assert outputs['pdf'].startswith(b'%PDF-')
        assert b'<svg' in outputs['html']
        reader = PdfReader(io.BytesIO(outputs['pdf']))
        assert '432.1' in ''.join(page.extract_text() for page in reader.pages)
