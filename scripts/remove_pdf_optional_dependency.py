from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'ml_lab/report_exports.py'
s = p.read_text(encoding='utf-8')
start = s.index('def chart_drawing(chart):')
end = s.index('def chart_svg(chart):', start)
s = s[:start] + s[end:]
start = s.index('def export_pdf(report):')
end = s.index('def export_report(report, format):', start)
s = s[:start] + '''def export_pdf(report):
    # Use the integrated writer so application exports need no reportlab install.
    from ml_lab.portable_pdf import export_portable_pdf
    return export_portable_pdf(report)


''' + s[end:]
p.write_text(s, encoding='utf-8')
