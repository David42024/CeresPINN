import React, { useState } from 'react';
import { RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';

export function useFigureZoom<T>(records: T[]) {
  const [zoom, setZoom] = useState(1);
  const [position, setPosition] = useState(0);
  const count = Math.min(records.length, Math.max(2, Math.ceil(records.length / zoom)));
  const maxStart = Math.max(0, records.length - count);
  const start = Math.min(position, maxStart);
  const changeZoom = (nextZoom: number) => {
    const nextCount = Math.min(records.length, Math.max(2, Math.ceil(records.length / nextZoom)));
    setPosition(Math.max(0, Math.min(records.length - nextCount, Math.round(start + (count - nextCount) / 2))));
    setZoom(nextZoom);
  };
  return {
    records: records.slice(start, start + count), zoom, start, maxStart,
    canZoomIn: zoom < 8 && count > 2,
    zoomIn: () => changeZoom(Math.min(8, zoom * 2)),
    zoomOut: () => changeZoom(Math.max(1, zoom / 2)),
    reset: () => { setZoom(1); setPosition(0); },
    pan: setPosition,
  };
}

type FigureZoomControlsProps = Omit<ReturnType<typeof useFigureZoom>, 'records'> & { title: string };

export function FigureZoomControls({ title, zoom, start, maxStart, canZoomIn, zoomIn, zoomOut, reset, pan }: FigureZoomControlsProps) {
  const buttonClass = 'inline-flex items-center gap-1 rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 dark:border-slate-700 dark:text-slate-200 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800';
  return (
    <div role="group" aria-label={`Zoom de ${title}`} className="flex flex-wrap items-center gap-2">
      <button type="button" onClick={zoomIn} disabled={!canZoomIn} className={buttonClass} aria-label={`Acercar ${title}`}><ZoomIn size={14} /> Zoom +</button>
      <button type="button" onClick={zoomOut} disabled={zoom <= 1} className={buttonClass} aria-label={`Alejar ${title}`}><ZoomOut size={14} /> Zoom −</button>
      <button type="button" onClick={reset} disabled={zoom === 1} className={buttonClass} aria-label={`Restablecer ${title}`}><RotateCcw size={14} /> Restablecer</button>
      <span className="text-xs text-slate-600 dark:text-slate-300" aria-live="polite">{zoom}×</span>
      {maxStart > 0 && <input type="range" min={0} max={maxStart} value={start} onChange={event => pan(Number(event.target.value))} aria-label={`Desplazar período de ${title}`} className="w-32 accent-emerald-600" />}
    </div>
  );
}
