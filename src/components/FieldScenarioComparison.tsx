import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import { AlertTriangle, MapPin, TrendingDown, Globe, Info } from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  CartesianGrid, Legend, Cell
} from 'recharts';
import { Field, SimulationConfig } from '../types';
import { INITIAL_FIELDS } from '../data/mockData';
import { simulateScenario } from '../services/api';

interface FieldScenarioComparisonProps {
  fields: Field[];
  currentConfig: SimulationConfig;
}

const RISK_LEVEL = (yieldLoss: number, cwsi: number) => {
  if (yieldLoss > 22 || cwsi > 0.6) return { label: 'Estrés muy alto', color: '#ef4444', bg: 'bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-500/40' };
  if (yieldLoss > 14 || cwsi > 0.4) return { label: 'Estrés alto', color: '#f97316', bg: 'bg-orange-500/15 text-orange-700 dark:text-orange-300 border border-orange-500/40' };
  if (yieldLoss > 8 || cwsi > 0.25) return { label: 'Estrés medio', color: '#f59e0b', bg: 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/40' };
  return { label: 'Estrés bajo', color: '#10b981', bg: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40' };
};

type FieldComparisonDatum = {
  field: Field;
  ssp1Yield: number;
  activeYield: number;
  ssp5Yield: number;
  yieldLoss: number;
  cwsi: number;
  resilience: number;
  critDays: number;
  risk: ReturnType<typeof RISK_LEVEL>;
};

export const FieldScenarioComparison: React.FC<FieldScenarioComparisonProps> = ({ fields, currentConfig }) => {
  const { t } = useTranslation();
  const [activeScenario, setActiveScenario] = useState<'SSP1-2.6' | 'SSP3-7.0' | 'SSP5-8.5'>('SSP3-7.0');
  const [fieldData, setFieldData] = useState<FieldComparisonDatum[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const allFields = fields.length > 0 ? fields : INITIAL_FIELDS;

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError(null);

    Promise.all(allFields.map(async field => {
      const configSsp1 = { ...currentConfig, scenario: 'SSP1-2.6' as const, fieldId: field.id };
      const configActive = { ...currentConfig, scenario: activeScenario, fieldId: field.id };
      const configSsp5 = { ...currentConfig, scenario: 'SSP5-8.5' as const, fieldId: field.id };
      const [resSsp1, resActive, resSsp5] = await Promise.all([
        simulateScenario(field, configSsp1),
        simulateScenario(field, configActive),
        simulateScenario(field, configSsp5),
      ]);
      const yieldLoss = resActive.summaryKPIs.yieldLossDueToDroughtPercent;
      const cwsi = resActive.summaryKPIs.peakWaterStressIndex;
      return {
        field,
        ssp1Yield: resSsp1.summaryKPIs.projectedYieldKgHa,
        activeYield: resActive.summaryKPIs.projectedYieldKgHa,
        ssp5Yield: resSsp5.summaryKPIs.projectedYieldKgHa,
        yieldLoss,
        cwsi,
        resilience: resActive.summaryKPIs.droughtResilienceScore,
        critDays: resActive.summaryKPIs.criticalDroughtDaysCount,
        risk: RISK_LEVEL(yieldLoss, cwsi),
      };
    }))
      .then(data => { if (active) setFieldData(data.sort((a, b) => b.yieldLoss - a.yieldLoss)); })
      .catch(error => {
        if (active) setLoadError(error instanceof Error ? error.message : String(error));
      })
      .finally(() => { if (active) setLoading(false); });

    return () => { active = false; };
  }, [allFields, currentConfig, activeScenario]);

  // Bar chart: SSP1 vs active vs SSP5 per field
  const chartData = fieldData.map(d => ({
    name: d.field.name.split(' ').slice(0, 2).join(' '),
    'SSP1-2.6':      d.ssp1Yield,
    [activeScenario]: d.activeYield,
    'SSP5-8.5':      d.ssp5Yield,
  }));

  const scenarioColors: Record<string, string> = {
    'SSP1-2.6': '#10b981',
    'SSP2-4.5': '#3b82f6',
    'SSP3-7.0': '#f59e0b',
    'SSP5-8.5': '#ef4444',
  };

  return (
    <div id="field-scenario-comparison" className="space-y-5">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-rose-950/30 via-slate-900 to-amber-950/20 border border-rose-500/30 shadow-xl space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-xl font-black text-slate-100 flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-rose-400" />
              Comparación Demostrativa de Campos (Zea mays L.)
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl">
              <strong>¿Para qué sirve?</strong> Compara las salidas del mismo escenario entre cuatro perfiles demostrativos. El checkpoint de rendimiento no usa coordenadas ni suelo como entradas, por lo que esta vista no constituye una evaluación espacial validada.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">{t('fieldComparison.activeScenario')}</span>
            <select
              value={activeScenario}
              onChange={e => setActiveScenario(e.target.value as any)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono font-bold focus:ring-2 focus:ring-rose-500"
            >
              <option value="SSP1-2.6">🟢 SSP1-2.6</option>
              <option value="SSP3-7.0">🟡 SSP3-7.0</option>
              <option value="SSP5-8.5">🔴 SSP5-8.5</option>
            </select>
          </div>
        </div>
      </div>

      {loading && (
        <div className="text-xs text-cyan-600 dark:text-cyan-300">Calculando escenarios comparativos con el checkpoint remoto…</div>
      )}
      {loadError && (
        <div className="text-xs text-rose-600 dark:text-rose-300">El backend no pudo calcular la comparación: {loadError}</div>
      )}

      {/* Risk Table */}
      <div className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
          <Globe className="w-4 h-4 text-cyan-500" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Orden exploratorio de indicadores — {activeScenario}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950/60 text-slate-500 dark:text-slate-400 uppercase text-[11px] tracking-wider">
                <th className="px-4 py-3 text-left">#</th>
                <th className="px-4 py-3 text-left">{t('fieldComparison.fieldRegion')}</th>
                <th className="px-4 py-3 text-right">{t('fieldComparison.yieldKgHa')}</th>
                <th className="px-4 py-3 text-right">{t('fieldComparison.droughtLoss')}</th>
                <th className="px-4 py-3 text-right">{t('fieldComparison.maxCwsi')}</th>
                <th className="px-4 py-3 text-right">{t('fieldComparison.criticalDays')}</th>
                <th className="px-4 py-3 text-right">{t('fieldComparison.resilience')}</th>
                <th className="px-4 py-3 text-center">{t('fieldComparison.riskLevel')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
              {fieldData.map((d, i) => (
                <tr key={d.field.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-bold text-slate-400">#{i+1}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-start gap-2">
                      <MapPin className="w-3.5 h-3.5 text-rose-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-semibold text-slate-900 dark:text-slate-100">{d.field.name}</p>
                        <p className="text-slate-500 text-[11px]">{d.field.locationName}, {d.field.country}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-slate-800 dark:text-slate-200">
                    {d.activeYield.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-mono font-bold ${d.yieldLoss > 15 ? 'text-rose-600 dark:text-rose-400' : d.yieldLoss > 8 ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {d.yieldLoss.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-700 dark:text-slate-300">{d.cwsi.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-mono text-amber-600 dark:text-amber-400">{d.critDays}d</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <div className="w-16 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${d.resilience}%`, backgroundColor: d.risk.color }} />
                      </div>
                      <span className="font-mono text-[11px] text-slate-600 dark:text-slate-400">{d.resilience}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-0.5 rounded-md text-[11px] font-bold ${d.risk.bg}`}>{d.risk.label}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Comparison Chart */}
      <div className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-4">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <TrendingDown className="w-4 h-4 text-rose-500" />
          Comparativa Rendimiento: SSP1-2.6 vs {activeScenario} vs SSP5-8.5 por Campo
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" />
            <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v/1000).toFixed(1)}t`} />
            <Tooltip formatter={(v: number) => [`${v.toLocaleString()} kg/ha`]} contentStyle={{ fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 16 }} />
            <Bar dataKey="SSP1-2.6" fill="#10b981" radius={[3,3,0,0]} />
            <Bar dataKey={activeScenario} fill={scenarioColors[activeScenario]} radius={[3,3,0,0]} />
            <Bar dataKey="SSP5-8.5" fill="#ef4444" radius={[3,3,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-start gap-2 p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200/50 dark:border-blue-800/30 text-xs text-slate-600 dark:text-slate-400">
        <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
        <span>{t('fieldComparison.policyNote')}</span>
      </div>
    </div>
  );
};
