import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import {
  Lightbulb, TrendingUp, Droplets, Calendar, Sprout, ArrowRight,
  CheckCircle, ChevronDown, ChevronUp, Zap, ShieldCheck, DollarSign
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  CartesianGrid, Cell, LabelList
} from 'recharts';
import { SimulationResult, Field, SimulationConfig } from '../types';
import { simulateScenario } from '../services/api';

interface AdaptationPanelProps {
  simulation: SimulationResult;
  field: Field;
  baseConfig: SimulationConfig;
  onApplyStrategy?: (config: Partial<SimulationConfig>) => void;
}

const RISK_COLOR = (score: number) =>
  score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

const IMPACT_BADGE: Record<string, string> = {
  high:   'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40',
  medium: 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/40',
  low:    'bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-500/40',
};

export const AdaptationPanel: React.FC<AdaptationPanelProps> = ({
  simulation, field, baseConfig, onApplyStrategy
}) => {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState<string | null>('early-planting');
  const [applying, setApplying] = useState<string | null>(null);
  const [strategyResults, setStrategyResults] = useState<SimulationResult[] | null>(null);
  const [strategyError, setStrategyError] = useState<string | null>(null);

  const baseYield = simulation.summaryKPIs.projectedYieldKgHa;

  // -----------------------------------------------------------------------
  // Three adaptation strategies — requested from the remote PINN.
  // -----------------------------------------------------------------------
  const strategyConfigs = useMemo(() => {
    const earlyConfig: SimulationConfig = {
      ...baseConfig,
      plantingDate: (() => {
        const d = new Date(baseConfig.plantingDate);
        d.setDate(d.getDate() - 14);
        return d.toISOString().slice(0, 10);
      })(),
    };
    const shortConfig: SimulationConfig = {
      ...baseConfig,
      maizeVariety: 'short_cycle',
    };
    const irrigConfig: SimulationConfig = {
      ...baseConfig,
      irrigationStrategy: 'deficit_75',
    };
    return [earlyConfig, shortConfig, irrigConfig];
  }, [baseConfig]);

  useEffect(() => {
    let active = true;
    setStrategyResults(null);
    setStrategyError(null);
    Promise.all(strategyConfigs.map(config => simulateScenario(field, config)))
      .then(results => { if (active) setStrategyResults(results); })
      .catch(error => {
        if (active) setStrategyError(error instanceof Error ? error.message : String(error));
      });
    return () => { active = false; };
  }, [field, strategyConfigs]);

  const strategies = useMemo(() => {
    if (!strategyResults) return [];
    const [earlyResult, shortResult, irrigResult] = strategyResults;
    const [earlyConfig, shortConfig, irrigConfig] = strategyConfigs;
    const earlyYield = earlyResult.summaryKPIs.projectedYieldKgHa;
    const shortYield = shortResult.summaryKPIs.projectedYieldKgHa;
    const irrigYield = irrigResult.summaryKPIs.projectedYieldKgHa;

    return [
      {
        id: 'early-planting',
        title: 'Adelanto de Siembra (−14 días)',
        description: 'Mover la fecha de siembra 14 días antes de la ventana óptima para que la floración evite el período de máxima temperatura y déficit hídrico de mediados de verano.',
        icon: Calendar,
        color: 'text-emerald-600 dark:text-emerald-400',
        bg: 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800/60',
        yield: earlyYield,
        delta: earlyYield - baseYield,
        deltaPct: ((earlyYield - baseYield) / baseYield * 100),
        waterSaved: baseResult => Math.round(baseResult.summaryKPIs.totalWaterConsumedMm * 0.05),
        impact: earlyYield > baseYield ? 'high' : earlyYield > baseYield * 0.97 ? 'medium' : 'low',
        resilienceScore: earlyResult.summaryKPIs.droughtResilienceScore,
        economicGain: earlyResult.summaryKPIs.economicReturnUsdHa - simulation.summaryKPIs.economicReturnUsdHa,
        config: earlyConfig,
      },
      {
        id: 'short-cycle',
        title: 'Variedad Ciclo Corto (~95 días)',
        description: 'Sustituir la variedad de ciclo medio/largo por un híbrido de ciclo corto tolerante a sequía (FAO 300-400). El ciclo completo termina antes de los períodos críticos de estrés terminal.',
        icon: Sprout,
        color: 'text-cyan-600 dark:text-cyan-400',
        bg: 'bg-cyan-50 dark:bg-cyan-950/40 border-cyan-200 dark:border-cyan-800/60',
        yield: shortYield,
        delta: shortYield - baseYield,
        deltaPct: ((shortYield - baseYield) / baseYield * 100),
        waterSaved: _b => Math.round(shortResult.summaryKPIs.totalWaterConsumedMm * 0.18),
        impact: shortYield > baseYield * 1.02 ? 'high' : shortYield > baseYield * 0.97 ? 'medium' : 'low',
        resilienceScore: shortResult.summaryKPIs.droughtResilienceScore,
        economicGain: shortResult.summaryKPIs.economicReturnUsdHa - simulation.summaryKPIs.economicReturnUsdHa,
        config: shortConfig,
      },
      {
        id: 'supplemental-irrig',
        title: 'Riego Suplementario en Floración (75% ETc)',
        description: 'Aplicar 1-3 riegos estratégicos durante la ventana VT-R1 (floración-silking) para mantener la humedad del suelo sobre el 75% de capacidad de campo. Maximiza la cuaja de grano.',
        icon: Droplets,
        color: 'text-blue-600 dark:text-blue-400',
        bg: 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800/60',
        yield: irrigYield,
        delta: irrigYield - baseYield,
        deltaPct: ((irrigYield - baseYield) / baseYield * 100),
        waterSaved: _b => -Math.round(irrigResult.summaryKPIs.totalIrrigationAppliedMm),
        impact: irrigYield > baseYield * 1.05 ? 'high' : irrigYield > baseYield * 1.0 ? 'medium' : 'low',
        resilienceScore: irrigResult.summaryKPIs.droughtResilienceScore,
        economicGain: irrigResult.summaryKPIs.economicReturnUsdHa - simulation.summaryKPIs.economicReturnUsdHa,
        config: irrigConfig,
      },
    ];
  }, [simulation, strategyConfigs, strategyResults]);

  // Bar chart data for quick comparison
  const chartData = [
    { name: 'Base', yield: baseYield, fill: '#64748b' },
    ...strategies.map(s => ({ name: s.title.split('(')[0].trim().split(' ').slice(0,2).join(' '), yield: s.yield, fill: s.delta >= 0 ? '#10b981' : '#ef4444' }))
  ];

  const handleApply = async (strategy: typeof strategies[0]) => {
    setApplying(strategy.id);
    await new Promise(r => setTimeout(r, 300));
    onApplyStrategy?.(strategy.config);
    setApplying(null);
  };

  return (
    <div id="adaptation-panel" className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="space-y-1">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" />
            Recomendaciones de Adaptación Climática (CeresPINN)
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 max-w-3xl">
            <strong>¿Para qué sirve?</strong> Cuantifica el impacto en rendimiento (Δ kg/ha) de 3 intervenciones agronómicas bajo el escenario climático activo, calculadas en tiempo real por el motor PINN.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 dark:text-slate-400">{t('adaptationPanel.baseYield')}</span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 font-mono font-bold text-sm text-slate-800 dark:text-slate-200">
            {baseYield.toLocaleString()} kg/ha
          </span>
        </div>
      </div>

      {!strategyResults && !strategyError && (
        <div className="text-xs text-cyan-600 dark:text-cyan-300">Consultando estrategias en el PINN de Render…</div>
      )}
      {strategyError && (
        <div className="text-xs text-rose-600 dark:text-rose-300">No se pudieron calcular estrategias con el PINN remoto: {strategyError}</div>
      )}

      {/* Comparison Bar Chart */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
        <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-3 flex items-center gap-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
          Comparativa de Rendimiento: Base vs. Estrategias de Adaptación
        </p>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 40, top: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} horizontal={false} />
            <XAxis type="number" domain={[Math.min(...chartData.map(d => d.yield)) * 0.92, Math.max(...chartData.map(d => d.yield)) * 1.02]} tick={{ fontSize: 10 }} tickFormatter={v => `${(v/1000).toFixed(1)}t`} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={80} />
            <Tooltip formatter={(v: number) => [`${v.toLocaleString()} kg/ha`, 'Rendimiento']} contentStyle={{ fontSize: 11 }} />
            <Bar dataKey="yield" radius={[0,4,4,0]}>
              {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              <LabelList dataKey="yield" position="right" formatter={(v: number) => `${v.toLocaleString()}`} style={{ fontSize: 10, fill: 'currentColor' }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Strategy Cards */}
      <div className="space-y-3">
        {strategies.map((strategy) => {
          const Icon = strategy.icon;
          const isOpen = expanded === strategy.id;
          return (
            <div key={strategy.id} className={`rounded-xl border ${strategy.bg} overflow-hidden transition-all`}>
              <button
                className="w-full p-4 flex items-center justify-between gap-3 text-left"
                onClick={() => setExpanded(isOpen ? null : strategy.id)}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg bg-white/60 dark:bg-slate-900/50`}>
                    <Icon className={`w-4 h-4 ${strategy.color}`} />
                  </div>
                  <div>
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100">{strategy.title}</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${IMPACT_BADGE[strategy.impact]}`}>
                        Impacto {strategy.impact === 'high' ? 'Alto' : strategy.impact === 'medium' ? 'Medio' : 'Bajo'}
                      </span>
                      <span className={`text-xs font-mono font-bold ${strategy.delta >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                        {strategy.delta >= 0 ? '+' : ''}{strategy.delta.toLocaleString()} kg/ha
                        ({strategy.deltaPct >= 0 ? '+' : ''}{strategy.deltaPct.toFixed(1)}%)
                      </span>
                    </div>
                  </div>
                </div>
                {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />}
              </button>

              {isOpen && (
                <div className="px-4 pb-4 space-y-3 border-t border-white/40 dark:border-slate-700/40 pt-3">
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">{strategy.description}</p>

                  {/* KPI row */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="p-2.5 rounded-lg bg-white/70 dark:bg-slate-900/60 text-center">
                      <span className="text-slate-500 block text-[11px]">{t('adaptationPanel.yield')}</span>
                      <strong className="font-mono text-slate-900 dark:text-slate-100">{strategy.yield.toLocaleString()}</strong>
                      <span className="text-slate-500 text-[10px]"> kg/ha</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white/70 dark:bg-slate-900/60 text-center">
                      <span className="text-slate-500 block text-[11px]">{t('adaptationPanel.resilience')}</span>
                      <strong className="font-mono" style={{ color: RISK_COLOR(strategy.resilienceScore) }}>{strategy.resilienceScore}</strong>
                      <span className="text-slate-500 text-[10px]">/100</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white/70 dark:bg-slate-900/60 text-center">
                      <span className="text-slate-500 block text-[11px]">{t('adaptationPanel.marginDelta')}</span>
                      <strong className={`font-mono ${strategy.economicGain >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                        {strategy.economicGain >= 0 ? '+' : ''}${strategy.economicGain}
                      </strong>
                      <span className="text-slate-500 text-[10px]">/ha</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleApply(strategy)}
                    disabled={applying === strategy.id}
                    className="w-full py-2 px-4 rounded-xl bg-slate-900 dark:bg-slate-100 hover:bg-slate-700 dark:hover:bg-white text-white dark:text-slate-900 font-bold text-xs flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-60"
                  >
                    {applying === strategy.id ? (
                      <><div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Aplicando...</>
                    ) : (
                      <><Zap className="w-3.5 h-3.5 text-amber-400" /> Aplicar Estrategia a Simulación Principal <ArrowRight className="w-3.5 h-3.5" /></>
                    )}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer note */}
      <div className="flex items-start gap-2 p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 text-xs text-slate-600 dark:text-slate-400">
        <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
        <span>{t('adaptationPanel.footerNote', { scenario: simulation.config.scenario, field: simulation.fieldName })}</span>
      </div>
    </div>
  );
};
