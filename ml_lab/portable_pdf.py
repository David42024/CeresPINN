"""Dependency-free PDF writer for text, tables and vector report figures."""
import io
import math
import textwrap
from xml.sax.saxutils import escape


def chart_geometry(chart):
    values = chart['values'] if chart['kind'] == 'bar' else [v for group in chart['values'] for v in group]
    if not values or not all(math.isfinite(float(v)) for v in values):
        raise ValueError('El gráfico necesita valores finitos.')
    low, high = min(0, min(values)), max(0, max(values))
    span = high - low or 1
    return low - span * .08, high + span * .08, max(180, 70 + 38 * len(chart['labels']))


def svg_chart(chart):
    import numpy as np
    low, high, height = chart_geometry(chart)
    x = lambda v: 160 + (v - low) / (high - low) * 315
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 510 {height}" role="img">',
             f'<title>{escape(chart["title"])}</title>']
    for i in range(5):
        value = low + (high - low) * i / 4
        position = x(value)
        parts.append(f'<path d="M{position} 20V{height-30}" stroke="#ddd"/>')
        parts.append(f'<text x="{position}" y="{height-10}" text-anchor="middle" font-size="9">{value:.3g}</text>')
    for i, label in enumerate(chart['labels']):
        y = 45 + i * 38
        parts.append(f'<text x="150" y="{y+3}" text-anchor="end" font-family="Arial" font-size="9">{escape(label)}</text>')
        if chart['kind'] == 'bar':
            left, right = sorted([x(0), x(chart['values'][i])])
            parts.append(f'<rect x="{left}" y="{y-8}" width="{max(.5,right-left)}" height="16" fill="#236b8e"/>')
        else:
            minimum, q1, median, q3, maximum = np.quantile(chart['values'][i], [0,.25,.5,.75,1])
            parts += [f'<path d="M{x(minimum)} {y}H{x(maximum)}" stroke="#333"/>',
                      f'<rect x="{x(q1)}" y="{y-8}" width="{max(.5,x(q3)-x(q1))}" height="16" fill="#c9e1eb" stroke="#333"/>',
                      f'<path d="M{x(median)} {y-8}V{y+8}" stroke="#333"/>']
    parts.append('</svg>')
    return ''.join(parts)


def export_portable_pdf(report):
    import numpy as np
    from ml_lab.report_exports import value_text, readable_date, TEMPLATES
    width, height, margin = 595, 842, 48
    available = width - 2 * margin
    pages, commands = [], []
    y = height - margin

    def encoded(text):
        raw = str(text).encode('cp1252', errors='replace').decode('cp1252')
        return raw.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)').replace('\r',' ').replace('\n',' ')

    def text(value, x, baseline, size=10, bold=False):
        font = 'F2' if bold else 'F1'
        commands.append(f'BT /{font} {size} Tf 1 0 0 1 {x:.2f} {baseline:.2f} Tm ({encoded(value)}) Tj ET')

    def page():
        nonlocal commands, y
        commands.append('.45 .45 .45 rg')
        text('CeresPINN · ' + TEMPLATES.get(report['metadata']['template'], 'Informe'), margin, 25, 8)
        text(str(len(pages) + 1), width - margin, 25, 8)
        commands.append('0 0 0 rg')
        pages.append('\n'.join(commands).encode('cp1252'))
        commands = []
        y = height - margin - 25
        text('CERESPINN / RESULTADOS DE INVESTIGACIÓN', margin, height-margin, 8, True)

    def ensure(space):
        if y - space < margin:
            page()

    def paragraph(value, size=10.5, bold=False):
        nonlocal y
        lines = textwrap.wrap(str(value), width=max(12, int(available / (size * .55))),
                              break_long_words=True) or ['']
        for line in lines:
            ensure(size * 1.4)
            text(line, margin, y, size, bold)
            y -= size * 1.48
        y -= 9

    active_header = None
    def row(cells, header=False, index=0):
        nonlocal y
        count = len(cells)
        widths = ([available * .56, available * .44] if count == 2 else
                  [available * .31] + [available * .69 / (count-1)] * (count-1))
        lines = [textwrap.wrap(value_text(v), width=max(8,int((w-14)/4.5))) or [''] for v,w in zip(cells,widths)]
        cell_height = max(map(len,lines))*11 + 16
        if y - cell_height < margin:
            page()
            if not header and active_header:
                row(active_header, True)
        if header:
            commands.append(f'.91 .94 .93 rg {margin} {y-cell_height:.2f} {available} {cell_height} re f 0 0 0 rg')
        elif index % 2:
            commands.append(f'.97 .98 .98 rg {margin} {y-cell_height:.2f} {available} {cell_height} re f 0 0 0 rg')
        for i, group in enumerate(lines):
            x = margin + sum(widths[:i])
            commands.append(f'.82 .84 .84 RG .35 w {x:.2f} {y-cell_height:.2f} {widths[i]:.2f} {cell_height} re S 0 0 0 RG')
            for offset, line in enumerate(group):
                text(line, x+7, y-14-offset*11, 8, header)
        y -= cell_height

    commands.append('.18 .42 .35 rg')
    text('CERESPINN  /  ' + TEMPLATES.get(report['metadata']['template'], 'Informe').upper(), margin, y, 9, True)
    commands.append('0 0 0 rg')
    y -= 38
    paragraph(report['metadata']['title'], 25, True)
    commands.append('.4 .4 .4 rg')
    if report['metadata']['author'].strip():
        paragraph('Preparado por ' + report['metadata']['author'], 10)
    paragraph(readable_date(report['metadata']['generated_at']), 9)
    commands.append('0 0 0 rg')
    y -= 18
    for section_number, section in enumerate(report['sections'], 1):
        ensure(100)
        y -= 9
        paragraph(f'{section_number:02d}  {section["title"]}', 13, True)
        paragraph(section['text'])
        if report['options']['include_tables'] and section.get('rows'):
            active_header = section['columns']
            row(section['columns'], True)
            for index, cells in enumerate(section['rows']):
                row(cells, index=index)
            y -= 20
            active_header = None
    if report['options']['include_charts']:
        for chart in report['charts']:
            low, high, chart_height = chart_geometry(chart)
            factor = min(available/510, 600/chart_height)
            ensure(chart_height*factor + 50)
            paragraph(chart['title'], 13, True)
            top = y
            x = lambda value: margin + (160+(value-low)/(high-low)*315)*factor
            for i in range(5):
                value = low+(high-low)*i/4
                position = x(value)
                commands.append(f'.85 .85 .85 RG {position:.2f} {top-20*factor:.2f} m {position:.2f} {top-(chart_height-30)*factor:.2f} l S 0 0 0 RG')
                text(f'{value:.3g}', position-10, top-(chart_height-10)*factor, 8)
            for i, label in enumerate(chart['labels']):
                baseline = top-(45+i*38)*factor
                text(label, margin, baseline-3, 8)
                if chart['kind'] == 'bar':
                    left,right = sorted([x(0),x(chart['values'][i])])
                    commands.append(f'.137 .42 .557 rg {left:.2f} {baseline-8*factor:.2f} {max(.5,right-left):.2f} {16*factor:.2f} re f 0 0 0 rg')
                else:
                    minimum,q1,median,q3,maximum=np.quantile(chart['values'][i],[0,.25,.5,.75,1])
                    commands.append(f'{x(minimum):.2f} {baseline:.2f} m {x(maximum):.2f} {baseline:.2f} l S')
                    commands.append(f'.79 .88 .92 rg {x(q1):.2f} {baseline-8*factor:.2f} {max(.5,x(q3)-x(q1)):.2f} {16*factor:.2f} re B 0 0 0 rg')
                    commands.append(f'{x(median):.2f} {baseline-8*factor:.2f} m {x(median):.2f} {baseline+8*factor:.2f} l S')
            y -= chart_height*factor + 12
    page()
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>']
    kids=[]
    for content in pages:
        page_id=len(objects)+1
        stream_id=page_id+1
        kids.append(f'{page_id} 0 R')
        objects.append((f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] '
            f'/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {stream_id} 0 R >>').encode())
        objects.append(f'<< /Length {len(content)} >>\nstream\n'.encode()+content+b'\nendstream')
    objects[1]=f'<< /Type /Pages /Count {len(pages)} /Kids [{" ".join(kids)}] >>'.encode()
    output=io.BytesIO()
    output.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(output.tell())
        output.write(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    xref=output.tell()
    output.write(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        output.write(f'{offset:010d} 00000 n \n'.encode())
    output.write(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return output.getvalue()
