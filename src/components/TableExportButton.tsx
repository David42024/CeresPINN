import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Download } from 'lucide-react';
import { downloadExcel, ExportRow } from '../utils/figureExport';

interface TableExportButtonProps {
  rows: ExportRow[];
  fileName: string;
}

export const TableExportButton: React.FC<TableExportButtonProps> = ({ rows, fileName }) => {
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="text-right">
      <button
        type="button"
        onClick={async () => {
          try {
            setError(null);
            await downloadExcel(rows, fileName);
          } catch (exportError) {
            console.error('No se pudo exportar la tabla Excel:', exportError);
            setError(exportError instanceof Error ? exportError.message : 'Error inesperado al exportar.');
          }
        }}
        className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <Download className="h-3.5 w-3.5" /> {t('exportData.downloadExcel')}
      </button>
      {error && <span role="alert" className="mt-1 block text-[10px] text-rose-600 dark:text-rose-400">{error}</span>}
    </div>
  );
};
