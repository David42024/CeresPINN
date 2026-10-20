import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { downloadCsv, ExportRow } from '../utils/figureExport';

interface TableExportButtonProps {
  rows: ExportRow[];
  fileName: string;
}

export const TableExportButton: React.FC<TableExportButtonProps> = ({ rows, fileName }) => {
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="text-right">
      <button
        type="button"
        onClick={() => {
          try {
            setError(null);
            downloadCsv(rows, fileName);
          } catch (exportError) {
            console.error('No se pudo exportar la tabla CSV:', exportError);
            setError(exportError instanceof Error ? exportError.message : 'Error inesperado al exportar.');
          }
        }}
        className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <Download className="h-3.5 w-3.5" /> Exportar CSV
      </button>
      {error && <span role="alert" className="mt-1 block text-[10px] text-rose-600 dark:text-rose-400">{error}</span>}
    </div>
  );
};
