import React from 'react';
import { ExportRow } from '../utils/figureExport';
import { TableExportButton } from './TableExportButton';

export function ExportDataTable({ title, rows, fileName }: { title: string; rows: ExportRow[]; fileName: string }) {
  const headers = Object.keys(rows[0] ?? {});
  return (
    <section aria-label={title} className="min-w-0 rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{title}</h4>
        <TableExportButton rows={rows} fileName={fileName} />
      </div>
      <p className="text-xs text-slate-600 dark:text-slate-400">{rows.length} registros. Excel incluye todos los días del escenario.</p>
      <div role="region" aria-label={`Datos de ${title}`} tabIndex={0} className="max-h-72 overflow-auto rounded-lg border border-slate-200 dark:border-slate-800">
        <table className="w-full text-left text-xs text-slate-700 dark:text-slate-200">
          <caption className="sr-only">{title}</caption>
          <thead className="sticky top-0 bg-slate-100 dark:bg-slate-800"><tr>{headers.map(header => <th key={header} scope="col" className="px-3 py-2">{header}</th>)}</tr></thead>
          <tbody>{rows.map((row, index) => <tr key={index} className="border-t border-slate-200 dark:border-slate-800">{headers.map(header => <td key={header} className="px-3 py-2 tabular-nums">{typeof row[header] === 'number' ? row[header].toLocaleString('es-PE', { maximumFractionDigits: 3 }) : String(row[header] ?? '')}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}
