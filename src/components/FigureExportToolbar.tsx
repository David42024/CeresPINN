import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, FileImage, FileText, Table } from 'lucide-react';
import {
  downloadCsv,
  downloadFigurePdf,
  downloadFigurePng,
  downloadFigureSvg,
  ExportRow,
  FigureExportOptions,
} from '../utils/figureExport';

interface FigureExportToolbarProps {
  targetRef: React.RefObject<HTMLElement | null>;
  options: FigureExportOptions;
  dataRows?: ExportRow[];
}

export const FigureExportToolbar: React.FC<FigureExportToolbarProps> = ({
  targetRef,
  options,
  dataRows,
}) => {
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);

  const runExport = async (action: (target: HTMLElement) => void | Promise<void>) => {
    const target = targetRef.current;
    if (!target) {
      setError(t('exportData.figureMissing'));
      return;
    }
    try {
      setError(null);
      await action(target);
    } catch (exportError) {
      console.error('No se pudo exportar la figura:', exportError);
      setError(exportError instanceof Error ? exportError.message : 'Error inesperado al exportar.');
    }
  };

  const buttonClass = 'inline-flex items-center gap-1 rounded-md border border-slate-300 px-2 py-1 text-[10px] font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800';

  return (
    <div className="flex flex-wrap items-center justify-end gap-1.5">
      <button type="button" className={buttonClass} onClick={() => void runExport(target => downloadFigureSvg(target, options))} aria-label={t('exportData.exportFigure', { title: options.title, format: 'SVG' })}>
        <FileImage className="h-3 w-3" /> SVG
      </button>
      <button type="button" className={buttonClass} onClick={() => void runExport(target => downloadFigurePng(target, options))} aria-label={t('exportData.exportFigure', { title: options.title, format: 'PNG 600 DPI' })}>
        <Download className="h-3 w-3" /> PNG 600 DPI
      </button>
      <button type="button" className={buttonClass} onClick={() => void runExport(target => downloadFigurePdf(target, options))} aria-label={t('exportData.exportFigure', { title: options.title, format: 'PDF' })}>
        <FileText className="h-3 w-3" /> PDF
      </button>
      {dataRows && (
        <button type="button" className={buttonClass} onClick={() => {
          try {
            setError(null);
            downloadCsv(dataRows, options.fileName);
          } catch (exportError) {
            console.error('No se pudo exportar la tabla CSV:', exportError);
            setError(exportError instanceof Error ? exportError.message : 'Error inesperado al exportar.');
          }
        }} aria-label={t('exportData.exportTable', { title: options.title, format: 'CSV' })}>
          <Table className="h-3 w-3" /> CSV
        </button>
      )}
      {error && <span role="alert" className="w-full text-right text-[10px] text-rose-600 dark:text-rose-400">{error}</span>}
    </div>
  );
};
