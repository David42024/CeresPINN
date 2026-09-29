"""Portable reports built exclusively from recorded ML Lab results."""
import base64
import hashlib
import html
import io
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

TEMPLATES = {
    'executive': 'Resumen ejecutivo',
    'technical': 'Informe técnico',
    'audit': 'Auditoría de reproducibilidad',
}


def readable_date(value):
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        date = date.astimezone(timezone(timedelta(hours=-5)))
        months = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
                  'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        return f'{date.day} de {months[date.month-1]} de {date.year} · {date:%H:%M} (UTC-5)'
    except (ValueError, TypeError, AttributeError):
        return 'Fecha no registrada'


def partition_description(partitions):
    labels = {'train': 'Entrenamiento', 'validation': 'Validación', 'test': 'Prueba'}
    parts = []
    for key, item in partitions.items():
        years = item.get('years', [])
        period = f'{min(years)}–{max(years)}' if years else 'periodo no registrado'
        rows = f"; {item['rows']:,} observaciones" if 'rows' in item else ''
        parts.append(f'{labels.get(key, key)}: {period}{rows}')
    return '. '.join(parts)


def build_report(root, df=None, template='technical', include_charts=True,
                 include_tables=True, title='Informe de CeresPINN', author=''):
    if template not in TEMPLATES:
        raise ValueError('Plantilla desconocida.')
    root = Path(root)
    folder = root / 'ml_lab' / 'artifacts'
    paths = [folder / 'common_benchmark.json', folder / 'statistical_analysis.json']
    paths += sorted(folder.glob('cv_*.json'))
    paths += [root / 'backend' / 'models' / 'cerespinn_spatial_v4_metadata.json',
              root / 'backend' / 'models' / 'cerespinn_metadata.json']
    sources, records, unavailable = [], {}, []
    for path in paths:
        if not path.exists():
            unavailable.append(path.name)
            continue
        raw = path.read_bytes()
        try:
            records[path.name] = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f'Archivo de resultados inválido: {path.name}') from exc
        sources.append({'file': str(path.relative_to(root)), 'sha256': hashlib.sha256(raw).hexdigest()})
    report = {'metadata': {'title': title, 'author': author,
        'generated_at': datetime.now(timezone.utc).isoformat(), 'template': template},
        'options': {'include_charts': include_charts, 'include_tables': include_tables},
        'sections': [], 'charts': [], 'sources': sources, 'unavailable': unavailable}
    sections = report['sections']
    sections.append({'title': 'Resumen de la evaluación', 'text':
        ('El benchmark común está disponible. El informe presenta el modelo seleccionado y '
         'su desempeño en datos de prueba independientes.' if records.get('common_benchmark.json') else
         'Este informe reúne los datos y resultados disponibles. La selección del mejor modelo '
         'aún está pendiente de ejecutar la comparación común de candidatos.')})
    if df is not None:
        coverage = ''
        if 'year' in df:
            import pandas as pd
            years = pd.to_numeric(df['year'], errors='coerce').dropna()
            if not years.empty:
                coverage = f' Cobertura: {int(years.min())}–{int(years.max())}.'
        if 'fips' in df:
            coverage += f" {df['fips'].nunique():,} condados representados."
        sections.append({'title': 'Datos activos', 'text': f'{len(df)} observaciones y {len(df.columns)} variables. '
            f'{int(df.duplicated().sum())} duplicados exactos adicionales.' + coverage,
            'columns': ['Variable', 'Valores faltantes'],
            'rows': [[str(c), int(df[c].isna().sum())] for c in df.columns] if template != 'executive' else []})
    benchmark = records.get('common_benchmark.json')
    if benchmark:
        sections.append({'title': 'Comparación de modelos', 'text':
            f"Evaluación registrada el {readable_date(benchmark.get('created_at'))}. "
            f"Ganador seleccionado por validación: {benchmark.get('winner', 'no registrado')}. "
            'Todos los candidatos comparten las particiones de evaluación. '
            f"{partition_description(benchmark.get('partitions', {}))}.",
            'columns': ['Modelo', 'R² validación', 'R² prueba', 'RMSE prueba kg/ha', 'MAE prueba kg/ha'],
            'rows': [[r['model'], r.get('validation_r2'), r.get('test_r2'),
                      r.get('test_rmse_kg_ha'), r.get('test_mae_kg_ha')] for r in benchmark['results']]})
        if include_charts:
            report['charts'].append({'title': 'R² en prueba independiente', 'kind': 'bar',
                'labels': [r['model'] for r in benchmark['results']],
                'values': [r['test_r2'] for r in benchmark['results']], 'ylabel': 'R²'})
    if template == 'executive':
        cv_records = [result for name, result in records.items() if name.startswith('cv_')]
        statistics_summary = records.get('statistical_analysis.json')
        if cv_records or statistics_summary:
            details = []
            for result in cv_records:
                protocol_label = 'temporal' if result['protocol'] == 'temporal' else 'espacial'
                details.append(f"Validación {protocol_label}: {result['outer_folds']} folds externos, "
                               f"{'con búsqueda anidada' if result['nested'] else 'con parámetros fijos'}.")
            if statistics_summary:
                tests = statistics_summary['results'] + statistics_summary.get('paired_results', [])
                rejected = sum(bool(test.get('reject')) for test in tests)
                details.append(f"Suite estadística: {len(tests)} contrastes; {rejected} rechazos de H0 "
                               f"con corrección Holm y alfa {statistics_summary['alpha']}.")
            sections.append({'title': 'Evaluaciones complementarias', 'text': ' '.join(details) +
                ' Los resultados por modelo y los intervalos completos se incluyen en la plantilla técnica.'})
    if template != 'executive':
        for name, result in records.items():
            if not name.startswith('cv_'):
                continue
            import pandas as pd
            folds = pd.DataFrame(result['results'])
            summary = folds.groupby('model').agg(r2=('r2', 'mean'), rmse=('rmse_kg_ha', 'mean'),
                                                 mae=('mae_kg_ha', 'mean')).reset_index()
            sections.append({'title': f"Validación {result['protocol']} {'anidada' if result['nested'] else 'con parámetros fijos'}",
                'text': f"Evaluación registrada el {readable_date(result.get('created_at'))}. "
                        f"Métrica: {result['metric_name']}. Folds externos: {result['outer_folds']}; "
                        f"internos: {result['inner_folds']}.",
                'columns': ['Modelo', 'R² externo medio', 'RMSE medio kg/ha', 'MAE medio kg/ha'],
                'rows': summary.values.tolist()})
            if include_charts:
                report['charts'].append({'title': f"R² externo {result['metric_name']}", 'kind': 'box',
                    'labels': summary['model'].tolist(),
                    'values': [folds.loc[folds.model == m, 'r2'].tolist() for m in summary['model']], 'ylabel': 'R²'})
    statistics = records.get('statistical_analysis.json')
    if statistics and template != 'executive':
        sections.append({'title': 'Inferencia estadística', 'text':
            f"Análisis registrado el {readable_date(statistics.get('created_at'))}. "
            f"Alfa: {statistics['alpha']}; réplicas: {statistics['replicates']}. "
            'Intervalos marginales; decisiones corregidas con Holm. Remuestreo agrupado por condado y año.',
            'columns': ['Prueba', 'Estimación', 'IC inferior', 'IC superior', 'p Holm', 'Decisión'],
            'rows': [[r['test'], r.get('estimate'), r.get('ci_lower'), r.get('ci_upper'),
                      r.get('p_holm'), 'Rechazar H0' if r.get('reject') else 'No rechazar H0']
                     for r in statistics['results'] + statistics.get('paired_results', [])]})
    metadata = records.get('cerespinn_spatial_v4_metadata.json')
    if metadata and template != 'executive':
        sections.append({'title': 'Modelo guardado', 'text':
            f"Algoritmo: {metadata.get('algorithm', 'no registrado')}. "
            f"Entrenado: {metadata.get('trained_at', 'sin fecha')}. "
            f"Protocolo: {metadata.get('evaluation_protocol', 'no registrado')}.",
            'columns': ['Métrica registrada', 'Valor'], 'rows': list(metadata.get('metrics', {}).items())})
    checkpoint = records.get('cerespinn_metadata.json')
    if checkpoint and not metadata:
        evaluation = checkpoint.get('evaluation', {}).get('split', {})
        method = evaluation.get('method', 'no registrado')
        method_label = {'grouped-random-year-holdout': 'reserva aleatoria de años'}.get(method, method)
        rows = []
        for label, key in [('Entrenamiento', 'train_metrics'), ('Prueba registrada', 'test_metrics')]:
            metric = checkpoint.get(key, {})
            rows.append([label, metric.get('r2'), metric.get('mae'), metric.get('mse')])
        units = 'bu/acre' if checkpoint.get('target_name') == 'yield_bu_acre' else checkpoint.get('target_name', 'unidad no registrada')
        sections.append({'title': 'Resultados del checkpoint disponible', 'text':
            f"Modelo: {checkpoint.get('model', 'sin nombre')}. "
            f"Partición registrada: {method_label}. "
            f"Entrenamiento: {checkpoint.get('train_rows', 'no registrado')} observaciones; "
            f"prueba: {checkpoint.get('test_rows', 'no registrado')}. "
            'Son métricas históricas registradas, no recalculadas en este informe ni equivalentes '
            'al nuevo benchmark común.', 'columns': ['Conjunto', 'R²', f'MAE ({units})', f'MSE ({units})²'], 'rows': rows})
        if include_charts and all(isinstance(row[1], (int, float)) for row in rows):
            report['charts'].append({'title': 'R² registrado del checkpoint', 'kind': 'bar',
                'labels': [row[0] for row in rows], 'values': [row[1] for row in rows], 'ylabel': 'R²'})
    pending = []
    if not benchmark:
        pending.append('Ejecutar la comparación común para seleccionar el mejor modelo.')
    if not any(name.startswith('cv_') for name in records):
        pending.append('Registrar validación cruzada temporal o espacial.')
    if not statistics:
        pending.append('Ejecutar la suite estadística para obtener intervalos y contrastes.')
    sections.append({'title': 'Próximos pasos', 'text': ' '.join(pending) if pending else
        'Revisar las diferencias entre modelos y documentar los resultados con el protocolo utilizado.'})
    sections.append({'title': 'Interpretación y límites', 'text':
        'Cada resultado debe interpretarse dentro de su protocolo y sus unidades. '
        'Las asociaciones observacionales no demuestran causalidad. '
        'La evaluación exploratoria no sustituye validación para uso operativo.'})
    if template == 'audit':
        sections.append({'title': 'Trazabilidad de fuentes', 'text':
            'Las huellas SHA256 identifican los archivos utilizados al generar el informe.',
            'columns': ['Archivo', 'SHA256'], 'rows': [[s['file'], s['sha256']] for s in sources]})
        report['raw_records'] = records
    return report


def value_text(value):
    if value is None:
        return 'No disponible'
    if isinstance(value, float):
        return f'{value:.6g}'
    return str(value)


def chart_svg(chart):
    from ml_lab.portable_pdf import svg_chart
    return svg_chart(chart)


def export_markdown(report):
    meta = report['metadata']
    lines = ['# ' + meta['title'], f"Generado: {readable_date(meta['generated_at'])}"]
    if meta['author'].strip():
        lines.append('Autor: ' + meta['author'])
    for section in report['sections']:
        lines += ['## ' + section['title'], section['text']]
        if report['options']['include_tables'] and section.get('rows'):
            clean = lambda v: value_text(v).replace('|', '\\|').replace('\n', ' ')
            lines += ['| ' + ' | '.join(section['columns']) + ' |',
                      '| ' + ' | '.join(['---'] * len(section['columns'])) + ' |']
            lines += ['| ' + ' | '.join(clean(v) for v in row) + ' |' for row in section['rows']]
    if report['options']['include_charts']:
        for chart in report['charts']:
            data = base64.b64encode(chart_svg(chart).encode('utf-8')).decode('ascii')
            lines.append(f"![{chart['title']}](data:image/svg+xml;base64,{data})")
    return '\n\n'.join(lines).encode('utf-8')


def export_html(report):
    esc = html.escape
    body = [f"<h1>{esc(report['metadata']['title'])}</h1>",
            f"<p>{esc(readable_date(report['metadata']['generated_at']))}</p>"]
    if report['metadata']['author'].strip():
        body.append(f"<p>Autor: {esc(report['metadata']['author'])}</p>")
    for section in report['sections']:
        body += [f"<h2>{esc(section['title'])}</h2>", f"<p>{esc(section['text'])}</p>"]
        if report['options']['include_tables'] and section.get('rows'):
            body.append('<table><thead><tr>' + ''.join(f'<th>{esc(c)}</th>' for c in section['columns']) + '</tr></thead><tbody>')
            body += ['<tr>' + ''.join(f'<td>{esc(value_text(v))}</td>' for v in row) + '</tr>' for row in section['rows']]
            body.append('</tbody></table>')
    if report['options']['include_charts']:
        for chart in report['charts']:
            body.append(f'<figure><figcaption>{esc(chart["title"])}</figcaption>{chart_svg(chart)}</figure>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>' + esc(report['metadata']['title']) +
        '</title><style>body{font:15px Arial;max-width:1100px;margin:36px auto;padding:20px;color:#111}'
        'table{border-collapse:collapse;width:100%;font-size:13px}td,th{border:1px solid #bbb;padding:7px;overflow-wrap:anywhere}'
        'th{background:#eee}img,svg{max-width:100%;height:auto}h2{margin-top:28px}</style></head><body>' + ''.join(body) + '</body></html>').encode('utf-8')


def export_pdf(report):
    # Use the integrated writer so application exports need no reportlab install.
    from ml_lab.portable_pdf import export_portable_pdf
    return export_portable_pdf(report)


def export_report(report, format):
    if format == 'json':
        return json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
    return {'markdown': export_markdown, 'html': export_html, 'pdf': export_pdf}[format](report)
