"""Streamlit report generation, preview, downloads and persisted history."""
import json
import importlib
from pathlib import Path
import streamlit as st
report_exports = importlib.import_module('ml_lab.report_exports')
TEMPLATES = report_exports.TEMPLATES
build_report = report_exports.build_report
export_report = report_exports.export_report
readable_date = report_exports.readable_date

ROOT = Path(__file__).resolve().parents[1]
FORMATS = {'markdown': ('md', 'text/markdown'), 'html': ('html', 'text/html'),
           'json': ('json', 'application/json'), 'pdf': ('pdf', 'application/pdf')}


def render_report_config(spec=None):
    template = st.selectbox('Plantilla', list(TEMPLATES), format_func=TEMPLATES.get)
    st.caption({'executive': 'Resumen del benchmark, modelo seleccionado y límites.',
        'technical': 'Datos, benchmark, validación cruzada, estadísticas y modelo guardado.',
        'audit': 'Informe técnico con huellas de fuentes y registros completos en JSON.'}[template])
    return {'template': template, 'title': st.text_input('Título', 'Informe de CeresPINN'),
            'author': st.text_input('Autor o equipo'),
            'include_charts': st.checkbox('Incluir gráficos', value=True),
            'include_tables': st.checkbox('Incluir tablas', value=True)}


def render_report_preview(report, key_prefix='report_preview'):
    import pandas as pd
    st.subheader(report['metadata']['title'])
    st.caption(readable_date(report['metadata']['generated_at']))
    if report['metadata']['author'].strip():
        st.caption('Preparado por ' + report['metadata']['author'])
    for section in report['sections']:
        st.markdown('### ' + section['title'])
        st.write(section['text'])
        if report['options']['include_tables'] and section.get('rows'):
            st.dataframe(pd.DataFrame(section['rows'], columns=section['columns']), width='stretch')
    if report['options']['include_charts']:
        import plotly.express as px
        for chart_index, chart in enumerate(report['charts']):
            if chart['kind'] == 'bar':
                fig = px.bar(x=chart['labels'], y=chart['values'], title=chart['title'],
                             labels={'x': 'Modelo', 'y': chart['ylabel']})
            else:
                values = [{'Modelo': label, 'R²': value} for label, group in zip(chart['labels'], chart['values']) for value in group]
                fig = px.box(pd.DataFrame(values), x='Modelo', y='R²', points='all', title=chart['title'])
            import uuid
            st.plotly_chart(fig, use_container_width=True, key=f'{key_prefix}_chart_{chart_index}_{uuid.uuid4().hex[:8]}')


def render_report_export(report, format=None):
    formats = [format] if format else list(FORMATS)
    for name in formats:
        try:
            content = export_report(report, name)
        except ImportError as exc:
            st.error(f'Exportación {name} requiere una dependencia declarada en ml_lab/requirements.txt: {exc}')
            continue
        extension, mime = FORMATS[name]
        st.download_button(f'Descargar {name.upper()}', content, f'reporte_cerespinn.{extension}', mime,
                           key=f"export_{report['metadata']['generated_at']}_{name}")


def render_report_history(artifact_manager=None, project_id=None):
    folder = ROOT / 'ml_lab' / 'reports'
    paths = sorted(folder.glob('report_*.json'), reverse=True) if folder.exists() else []
    if not paths:
        st.info('Todavía no hay reportes generados.')
        return
    for path in paths:
        with st.expander(path.stem):
            try:
                report = json.loads(path.read_text(encoding='utf-8'))
                render_report_preview(report, key_prefix=f'history_{path.stem}')
                for name, (extension, mime) in FORMATS.items():
                    output = path.with_suffix('.' + extension)
                    if output.exists():
                        st.download_button(f'Descargar {name.upper()}', output.read_bytes(), output.name,
                                           mime, key=f'history_{path.stem}_{name}')
            except (ValueError, KeyError) as exc:
                st.warning(f'No se puede mostrar este reporte: {exc}')


def render_report_generator_ui(spec=None, df=None):
    st.title('11. Reportes')
    generate, history = st.tabs(['Generar y descargar', 'Historial'])
    with generate:
        config = render_report_config(spec)
        if st.button('Generar reporte', type='primary'):
            try:
                with st.spinner('Generando reporte y exportaciones...'):
                    report = build_report(ROOT, df=df, **config)
                    outputs = {name: export_report(report, name) for name in FORMATS}
                    folder = ROOT / 'ml_lab' / 'reports'
                    folder.mkdir(parents=True, exist_ok=True)
                    stamp = report['metadata']['generated_at'].replace(':', '').replace('+', '_').replace('.', '')
                    base = folder / f'report_{stamp}'
                    for name, content in outputs.items():
                        base.with_suffix('.' + FORMATS[name][0]).write_bytes(content)
                    st.session_state['current_generated_report'] = report
                    st.session_state['current_report_exports'] = outputs
                st.success('Reporte generado con resultados guardados y PDF directo.')
            except Exception as exc:
                st.error(f'No se pudo generar el reporte: {exc}')
        report = st.session_state.get('current_generated_report')
        if report:
            render_report_preview(report, key_prefix='current_generated_report')
            for name, content in st.session_state['current_report_exports'].items():
                extension, mime = FORMATS[name]
                st.download_button(f'Descargar {name.upper()}', content, f'reporte_cerespinn.{extension}', mime)
    with history:
        render_report_history()
