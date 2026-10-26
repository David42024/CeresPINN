import jsPDF from 'jspdf';
import i18n from '../i18n';

export type ExportRow = Record<string, string | number | boolean | null | undefined>;

export interface FigureExportOptions {
  title: string;
  interpretation: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  fileName: string;
}

const SVG_NAMESPACE = 'http://www.w3.org/2000/svg';
const DPI_SCALE = 600 / 96;
const PIXELS_PER_METER = Math.round(600 / 0.0254);

const addPngDpiMetadata = (dataUrl: string) => {
  const base64 = dataUrl.split(',')[1];
  if (!base64) throw new Error('El navegador no generó un PNG válido.');

  const bytes = Uint8Array.from(atob(base64), character => character.charCodeAt(0));
  const readUint32 = (offset: number) =>
    ((bytes[offset] << 24) | (bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3]) >>> 0;
  if (String.fromCharCode(...bytes.slice(12, 16)) !== 'IHDR') {
    throw new Error('El PNG generado no contiene una cabecera IHDR válida.');
  }
  let insertionOffset = 8 + readUint32(8) + 12;
  let existingChunkLength = 0;
  for (let offset = insertionOffset; offset + 12 <= bytes.length;) {
    const chunkLength = readUint32(offset);
    const chunkName = String.fromCharCode(...bytes.slice(offset + 4, offset + 8));
    if (chunkName === 'pHYs') {
      insertionOffset = offset;
      existingChunkLength = chunkLength + 12;
      break;
    }
    if (chunkName === 'IDAT' || offset + chunkLength + 12 > bytes.length) break;
    offset += chunkLength + 12;
  }

  const chunkType = new TextEncoder().encode('pHYs');
  const chunkData = new Uint8Array(9);
  const chunkView = new DataView(chunkData.buffer);
  chunkView.setUint32(0, PIXELS_PER_METER);
  chunkView.setUint32(4, PIXELS_PER_METER);
  chunkData[8] = 1;

  const crcInput = new Uint8Array(chunkType.length + chunkData.length);
  crcInput.set(chunkType);
  crcInput.set(chunkData, chunkType.length);
  let crc = 0xffffffff;
  crcInput.forEach(byte => {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = crc & 1 ? (crc >>> 1) ^ 0xedb88320 : crc >>> 1;
    }
  });
  crc = (crc ^ 0xffffffff) >>> 0;

  const chunk = new Uint8Array(4 + 4 + chunkData.length + 4);
  new DataView(chunk.buffer).setUint32(0, chunkData.length);
  chunk.set(chunkType, 4);
  chunk.set(chunkData, 8);
  new DataView(chunk.buffer).setUint32(chunk.length - 4, crc);

  const result = new Uint8Array(bytes.length - existingChunkLength + chunk.length);
  result.set(bytes.slice(0, insertionOffset));
  result.set(chunk, insertionOffset);
  result.set(
    bytes.slice(insertionOffset + existingChunkLength),
    insertionOffset + chunk.length,
  );
  const resultBase64 = btoa(Array.from(result, byte => String.fromCharCode(byte)).join(''));
  return `data:image/png;base64,${resultBase64}`;
};

const getChartSvg = (container: HTMLElement): SVGSVGElement => {
  const svg = container.querySelector<SVGSVGElement>('.recharts-wrapper > svg.recharts-surface');
  if (!svg) {
    throw new Error('No se encontró una gráfica SVG para exportar.');
  }
  return svg;
};

const createExportSvg = (source: SVGSVGElement, options: FigureExportOptions): SVGSVGElement => {
  const bounds = source.getBoundingClientRect();
  const width = Math.max(1, Math.round(bounds.width));
  const height = Math.max(1, Math.round(bounds.height));
  const clone = source.cloneNode(true) as SVGSVGElement;
  const legend = Array.from(source.parentElement?.querySelectorAll<HTMLElement>('.recharts-legend-item-text') ?? []);
  const topPadding = legend.length ? 78 : 54;
  const bottomPadding = 56;
  const totalHeight = height + topPadding + bottomPadding;

  clone.setAttribute('xmlns', SVG_NAMESPACE);
  clone.setAttribute('width', String(width));
  clone.setAttribute('height', String(totalHeight));
  clone.setAttribute('viewBox', `0 0 ${width} ${totalHeight}`);
  clone.setAttribute('font-family', 'Arial, sans-serif');

  const definitions = Array.from(clone.children).filter(child => child.tagName.toLowerCase() === 'defs');
  const graphContent = Array.from(clone.children).filter(child => child.tagName.toLowerCase() !== 'defs');
  clone.replaceChildren(...definitions);

  const background = document.createElementNS(SVG_NAMESPACE, 'rect');
  background.setAttribute('width', '100%');
  background.setAttribute('height', '100%');
  background.setAttribute('fill', '#ffffff');
  clone.insertBefore(background, clone.firstChild);

  const addText = (text: string, x: number, y: number, size: number, weight = 'normal') => {
    const element = document.createElementNS(SVG_NAMESPACE, 'text');
    element.setAttribute('x', String(x));
    element.setAttribute('y', String(y));
    element.setAttribute('fill', '#111827');
    element.setAttribute('font-family', 'Arial, sans-serif');
    element.setAttribute('font-size', String(size));
    element.setAttribute('font-weight', weight);
    element.textContent = text;
    clone.appendChild(element);
  };

  addText(options.title, 18, 25, 16, 'bold');
  const axisDescription = [options.xAxisLabel, options.yAxisLabel].filter(Boolean).join(' | ');
  if (axisDescription) addText(axisDescription, 18, 44, 11);

  // Recharts renders legends in HTML, outside the chart SVG. Recreate their
  // labels and colors so downloaded figures identify every plotted series.
  let legendX = 18;
  legend.forEach(item => {
    const swatch = document.createElementNS(SVG_NAMESPACE, 'line');
    swatch.setAttribute('x1', String(legendX));
    swatch.setAttribute('x2', String(legendX + 18));
    swatch.setAttribute('y1', '63');
    swatch.setAttribute('y2', '63');
    swatch.setAttribute('stroke', getComputedStyle(item).color);
    swatch.setAttribute('stroke-width', '3');
    clone.appendChild(swatch);
    const label = item.textContent ?? '';
    addText(label, legendX + 24, 67, 10);
    legendX += label.length * 6 + 42;
  });

  const graph = document.createElementNS(SVG_NAMESPACE, 'g');
  graph.setAttribute('transform', `translate(0 ${topPadding})`);
  graphContent.forEach(child => graph.appendChild(child));
  clone.appendChild(graph);

  const words = options.interpretation.split(/\s+/);
  const maxChars = Math.max(35, Math.floor(width / 7));
  const lines: string[] = [];
  let line = '';
  words.forEach(word => {
    const candidate = line ? `${line} ${word}` : word;
    if (candidate.length > maxChars && line) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  });
  if (line) lines.push(line);
  lines.slice(0, 3).forEach((text, index) => addText(text, 18, height + topPadding + 18 + index * 14, 10));

  return clone;
};

const svgToPng = (svg: SVGSVGElement): Promise<{ dataUrl: string; width: number; height: number }> =>
  new Promise((resolve, reject) => {
    const source = new XMLSerializer().serializeToString(svg);
    const image = new Image();
    const url = URL.createObjectURL(new Blob([source], { type: 'image/svg+xml;charset=utf-8' }));
    image.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = Math.round(image.width * DPI_SCALE);
      canvas.height = Math.round(image.height * DPI_SCALE);
      const context = canvas.getContext('2d');
      if (!context) {
        URL.revokeObjectURL(url);
        reject(new Error('No se pudo crear el lienzo para generar el PNG.'));
        return;
      }
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.scale(DPI_SCALE, DPI_SCALE);
      context.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);
      resolve({ dataUrl: addPngDpiMetadata(canvas.toDataURL('image/png')), width: canvas.width, height: canvas.height });
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('No se pudo rasterizar la figura SVG.'));
    };
    image.src = url;
  });

export const createFigurePng = async (container: HTMLElement, options: FigureExportOptions) =>
  svgToPng(createExportSvg(getChartSvg(container), options));

const downloadBlob = (blob: Blob, fileName: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
};

export const downloadPngDataUrl600 = async (dataUrl: string, fileName: string) => {
  const response = await fetch(addPngDpiMetadata(dataUrl));
  if (!response.ok) throw new Error('No se pudo preparar la imagen PNG para descargar.');
  downloadBlob(await response.blob(), fileName);
};

export const downloadFigureSvg = (container: HTMLElement, options: FigureExportOptions) => {
  const svg = createExportSvg(getChartSvg(container), options);
  const source = new XMLSerializer().serializeToString(svg);
  downloadBlob(new Blob([source], { type: 'image/svg+xml;charset=utf-8' }), `${options.fileName}.svg`);
};

export const downloadFigurePng = async (container: HTMLElement, options: FigureExportOptions) => {
  const { dataUrl } = await createFigurePng(container, options);
  const response = await fetch(dataUrl);
  if (!response.ok) throw new Error('No se pudo preparar la imagen PNG para descargar.');
  downloadBlob(await response.blob(), `${options.fileName}_600dpi.png`);
};

export const downloadFigurePdf = async (container: HTMLElement, options: FigureExportOptions) => {
  const { dataUrl, width, height } = await createFigurePng(container, options);
  const pageWidth = 210;
  const margin = 10;
  const imageWidth = pageWidth - margin * 2;
  const imageHeight = imageWidth * height / width;
  const pageHeight = Math.max(297, imageHeight + margin * 2);
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: [pageWidth, pageHeight] });
  doc.addImage(dataUrl, 'PNG', margin, margin, imageWidth, imageHeight, undefined, 'FAST');
  doc.save(`${options.fileName}.pdf`);
};

export const downloadExcel = async (rows: ExportRow[], fileName: string) => {
  if (rows.length === 0) throw new Error('No hay datos disponibles para exportar.');
  const XLSX = await import('xlsx');
  const sheet = XLSX.utils.json_to_sheet(rows);
  sheet['!cols'] = Object.keys(rows[0]).map(header => ({ wch: Math.max(12, Math.min(48, header.length + 2)) }));
  sheet['!autofilter'] = { ref: sheet['!ref']! };
  const book = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(book, sheet, i18n.t('exportData.sheet'));
  XLSX.writeFile(book, `${fileName}.xlsx`);
};

export const downloadCsv = (rows: ExportRow[], fileName: string) => {
  if (rows.length === 0) throw new Error('No hay datos disponibles para exportar.');
  const headers = Object.keys(rows[0]);
  const escape = (value: ExportRow[keyof ExportRow]) => {
    const text = value == null ? '' : String(value);
    const safeText = typeof value === 'string' && /^[=+\-@]/.test(text) ? `'${text}` : text;
    return `"${safeText.replace(/"/g, '""')}"`;
  };
  const csv = [headers.map(escape).join(','), ...rows.map(row => headers.map(header => escape(row[header])).join(','))].join('\r\n');
  downloadBlob(new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }), `${fileName}.csv`);
};
