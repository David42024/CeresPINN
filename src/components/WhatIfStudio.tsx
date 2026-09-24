import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import { 
  GitCompare, 
  Sparkles, 
  TrendingUp, 
  Droplets, 
  DollarSign, 
  ShieldCheck, 
  Zap,
  Trophy,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  Scale,
  Award,
  AlertCircle
} from 'lucide-react';
import { 
  Field, 
  SimulationConfig, 
  SimulationResult, 
  ClimateScenario, 
  IrrigationStrategy, 
  MaizeVariety 
} from '../types';
import { simulateScenario } from '../services/api';

interface WhatIfStudioProps {
  field: Field;
  baseConfig: SimulationConfig;
  initialSimulation: SimulationResult;
}

export const WhatIfStudio: React.FC<WhatIfStudioProps> = ({ field, baseConfig, initialSimulation }) => {
  const { t } = useTranslation();

  // Scenario 1 (Baseline)
  const [configA, setConfigA] = useState<SimulationConfig>({ ...baseConfig });
  const [resultA, setResultA] = useState<SimulationResult>(initialSimulation);

  // Scenario 2 (Optimization 1 - Deficit or Date shift)
  const [configB, setConfigB] = useState<SimulationConfig>({
    ...baseConfig,
    irrigationStrategy: 'deficit_50',
    maizeVariety: 'medium_cycle'
  });
  const [resultB, setResultB] = useState<SimulationResult>(initialSimulation);

  // Scenario 3 (Optimization 2 - Sensor + Short cycle drought escape)
  const [configC, setConfigC] = useState<SimulationConfig>({
    ...baseConfig,
    irrigationStrategy: 'smart_sensor',
    maizeVariety: 'short_cycle'
  });
  const [resultC, setResultC] = useState<SimulationResult>(initialSimulation);

  // Comparison State
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [comparisonPending, setComparisonPending] = useState<boolean>(false);
  const [lastComparisonTime, setLastComparisonTime] = useState<string>('En tiempo real');
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  // Trigger PINN simulation for all 3 scenarios
  const handleRunComparison = async () => {
    setIsComparing(true);
    setComparisonError(null);
    try {
      // Simulate all 3 in parallel through the backend PINN.
      const [resA, resB, resC] = await Promise.all([
        simulateScenario(field, configA),
        simulateScenario(field, configB),
        simulateScenario(field, configC),
      ]);

      // Satisfying PINN tensor calculation latency for perceived physics calculation
      await new Promise((r) => setTimeout(r, 600));

      setResultA(resA);
      setResultB(resB);
      setResultC(resC);
      setComparisonPending(false);
      setLastComparisonTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } catch (err) {
      console.error('Comparison calculation failed:', err);
      setComparisonError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsComparing(false);
    }
  };

  useEffect(() => {
    void handleRunComparison();
    // Initial remote inference only; subsequent runs are user-triggered.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Local helper to update configs
  const handleUpdateConfigA = (updates: Partial<SimulationConfig>) => {
    const updated = { ...configA, ...updates };
    setConfigA(updated);
    setComparisonPending(true);
  };

  const handleUpdateConfigB = (updates: Partial<SimulationConfig>) => {
    const updated = { ...configB, ...updates };
    setConfigB(updated);
    setComparisonPending(true);
  };

  const handleUpdateConfigC = (updates: Partial<SimulationConfig>) => {
    const updated = { ...configC, ...updates };
    setConfigC(updated);
    setComparisonPending(true);
  };

  // Agronomic calculations for comparative analysis
  const yieldA = resultA.summaryKPIs.projectedYieldKgHa;
  const yieldB = resultB.summaryKPIs.projectedYieldKgHa;
  const yieldC = resultC.summaryKPIs.projectedYieldKgHa;

  const waterA = resultA.summaryKPIs.totalWaterConsumedMm;
  const waterB = resultB.summaryKPIs.totalWaterConsumedMm;
  const waterC = resultC.summaryKPIs.totalWaterConsumedMm;

  // Water Use Efficiency (WUE = kg grain / m³ of water consumed)
  // Note: 1 mm of water over 1 ha = 10 m³
  const wueA = waterA > 0 ? (yieldA / (waterA * 10)).toFixed(2) : '0.00';
  const wueB = waterB > 0 ? (yieldB / (waterB * 10)).toFixed(2) : '0.00';
  const wueC = waterC > 0 ? (yieldC / (waterC * 10)).toFixed(2) : '0.00';

  const marginA = resultA.summaryKPIs.economicReturnUsdHa;
  const marginB = resultB.summaryKPIs.economicReturnUsdHa;
  const marginC = resultC.summaryKPIs.economicReturnUsdHa;

  const cwsiA = resultA.summaryKPIs.peakWaterStressIndex;
  const cwsiB = resultB.summaryKPIs.peakWaterStressIndex;
  const cwsiC = resultC.summaryKPIs.peakWaterStressIndex;

  // Identify Best Scenario
  let winner = 'C';
  let winnerTitle = 'Escenario C (Sensor + Resiliencia)';
  let winnerYield = yieldC;
  let winnerWater = waterC;
  let winnerMargin = marginC;
  let winnerCwsi = cwsiC;
  let winnerWue = wueC;

  if (yieldB > yieldC && yieldB > yieldA) {
    winner = 'B';
    winnerTitle = 'Escenario B (Optimización 1)';
    winnerYield = yieldB;
    winnerWater = waterB;
    winnerMargin = marginB;
    winnerCwsi = cwsiB;
    winnerWue = wueB;
  } else if (yieldA >= yieldB && yieldA >= yieldC) {
    winner = 'A';
    winnerTitle = 'Escenario A (Línea Base)';
    winnerYield = yieldA;
    winnerWater = waterA;
    winnerMargin = marginA;
    winnerCwsi = cwsiA;
    winnerWue = wueA;
  }

  const deltaYieldVsBase = winnerYield - yieldA;
  const deltaYieldPct = yieldA > 0 ? ((deltaYieldVsBase / yieldA) * 100).toFixed(1) : '0.0';
  const deltaWaterVsBase = winnerWater - waterA;
  const deltaMarginVsBase = winnerMargin - marginA;
  const cwsiReductionPct = cwsiA > 0 ? (((cwsiA - winnerCwsi) / cwsiA) * 100).toFixed(0) : '0';

  // Max for visual progress bars
  const maxYield = Math.max(yieldA, yieldB, yieldC, 1);
  const maxMargin = Math.max(marginA, marginB, marginC, 1);
  const maxWater = Math.max(waterA, waterB, waterC, 1);

  return (
    <div id="what-if-analysis-studio" className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-6">
      {/* Header with Title and Comparison Action Button */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-2xl">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            {t('whatIfStudio.title', 'Módulo de Análisis Comparativo "¿Qué pasa si?" (What-If Studio)')}
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
            <strong>¿Para qué sirve?</strong> Evalúa y contrasta 3 estrategias agronómicas simultáneas bajo forzamiento climático PINN. Permite comparar la Línea Base con dos alternativas de adaptación observando la brecha de rendimiento (Δ kg/ha), el ahorro de agua y el margen económico en tiempo real.
          </p>
        </div>

        {/* COMPARISON TRIGGER BUTTON */}
        <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2.5">
          <button
            id="btn-run-what-if-comparison"
            onClick={handleRunComparison}
            disabled={isComparing}
            className={`px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm text-white shadow-lg transition-all active:scale-95 cursor-pointer flex items-center gap-2 ${
              isComparing
                ? 'bg-slate-700 cursor-not-allowed opacity-80'
                : 'bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 shadow-emerald-500/25 hover:shadow-emerald-500/40 ring-2 ring-emerald-400/30'
            }`}
            title="Lanzar simulación comparativa de los 3 escenarios mediante tensores PINN"
          >
            {isComparing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Simulando Redes PINN...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 text-amber-300 fill-amber-300 animate-pulse" />
                <span>⚡ Comparar 3 Escenarios Ahora</span>
              </>
            )}
          </button>

          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping inline-block" />
            <span>Último cálculo: <strong className="text-slate-700 dark:text-slate-300">{lastComparisonTime}</strong></span>
          </div>
        </div>
      </div>

      {/* Loading banner when running deep PINN comparison */}
      {isComparing && (
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/60 via-cyan-950/60 to-slate-900 border border-emerald-500/40 text-xs text-emerald-200 flex items-center gap-3 animate-pulse">
          <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
            <Sparkles className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <strong className="text-emerald-300 block font-semibold">Resolviendo Tensores de EDPs Acopladas PINN...</strong>
            <span className="text-[11px] text-slate-300">Comparando el balance hídrico demostrativo de 0-100 cm y la evapotranspiración parametrizada bajo tres escenarios climáticos.</span>
          </div>
        </div>
      )}

      {comparisonError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-600 dark:text-rose-300">
          No se pudo ejecutar la comparación con el PINN remoto: {comparisonError}
        </div>
      )}

      {/* Changes pending notification */}
      {comparisonPending && !isComparing && (
        <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-700/50 text-xs text-amber-900 dark:text-amber-300 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
            <span>Has modificado variables agronómicas. Haz clic en <strong>⚡ Comparar 3 Escenarios Ahora</strong> para consolidar la matriz comparativa de impacto.</span>
          </div>
          <button
            onClick={handleRunComparison}
            className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs transition-all shadow-xs cursor-pointer whitespace-nowrap"
          >
            Actualizar Comparativa
          </button>
        </div>
      )}

      {/* 3 Columns: Side-by-Side Scenario Configuration & Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Scenario A: Baseline */}
        <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-300 dark:hover:border-slate-700 transition-all">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
              <span className="px-2.5 py-0.5 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold text-xs flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-500 inline-block" />
                {t('whatIfStudio.scenarioABaseline', 'Escenario A (Línea Base)')}
              </span>
              <span className="text-xs font-mono text-slate-600 dark:text-slate-400">{configA.scenario}</span>
            </div>

            {/* Controls */}
            <div className="space-y-3 mt-3 text-xs">
              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.irrigationStrategyLabel', 'Estrategia de Riego')}</label>
                <select
                  value={configA.irrigationStrategy}
                  onChange={(e) => handleUpdateConfigA({ irrigationStrategy: e.target.value as IrrigationStrategy })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="rainfed">{t('whatIfStudio.optRainfed', 'Secano Estricto')}</option>
                  <option value="deficit_50">{t('whatIfStudio.optDeficit50', 'Riego Deficitario (50% ETc)')}</option>
                  <option value="optimal_100">{t('whatIfStudio.optOptimal100', 'Riego Óptimo (100% ETc)')}</option>
                  <option value="smart_sensor">{t('whatIfStudio.optSmartSensor', 'Sensor Inteligente (VT-R1)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.maizeVarietyLabel', 'Variedad de Maíz')}</label>
                <select
                  value={configA.maizeVariety}
                  onChange={(e) => handleUpdateConfigA({ maizeVariety: e.target.value as MaizeVariety })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="short_cycle">{t('whatIfStudio.optShortCycle', 'Ciclo Corto (90-100d)')}</option>
                  <option value="medium_cycle">{t('whatIfStudio.optMediumCycle', 'Ciclo Medio (110-120d)')}</option>
                  <option value="long_cycle">{t('whatIfStudio.optLongCycle', 'Ciclo Largo (130-140d)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.climateScenarioLabel', 'Escenario Climático CMIP6')}</label>
                <select
                  value={configA.scenario}
                  onChange={(e) => handleUpdateConfigA({ scenario: e.target.value as ClimateScenario })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="SSP1-2.6">{t('whatIfStudio.optSSP1', 'SSP1-2.6 (Optimista)')}</option>
                  <option value="SSP2-4.5">🔵 SSP2-4.5 (Moderado +1.4°C)</option>
                  <option value="SSP3-7.0">{t('whatIfStudio.optSSP3', 'SSP3-7.0 (Intermedio)')}</option>
                  <option value="SSP5-8.5">{t('whatIfStudio.optSSP5', 'SSP5-8.5 (Pesimista)')}</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary Box */}
          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.yieldLabel', 'Rendimiento:')}</span>
              <strong className="text-slate-900 dark:text-slate-100 font-mono text-sm">{resultA.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.waterConsumedLabel', 'Agua Consumida:')}</span>
              <strong className="text-cyan-700 dark:text-cyan-300 font-mono">{resultA.summaryKPIs.totalWaterConsumedMm} mm</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">Eficiencia Agua (WUE):</span>
              <strong className="text-slate-800 dark:text-slate-200 font-mono">{wueA} kg/m³</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.cwsiMaxLabel', 'Estrés Máximo CWSI:')}</span>
              <strong className="text-amber-600 dark:text-amber-400 font-mono">{resultA.summaryKPIs.peakWaterStressIndex.toFixed(2)}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.marginLabel', 'Margen Neto Est.:')}</span>
              <strong className="text-emerald-600 dark:text-emerald-400 font-mono">${resultA.summaryKPIs.economicReturnUsdHa} /ha</strong>
            </div>
          </div>
        </div>

        {/* Scenario B: Optimization 1 */}
        <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/80 border border-cyan-500/40 flex flex-col justify-between space-y-4 hover:border-cyan-500/70 transition-all">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
              <span className="px-2.5 py-0.5 rounded-lg bg-cyan-100 dark:bg-cyan-950 text-cyan-800 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-800 font-bold text-xs flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-500 inline-block" />
                {t('whatIfStudio.scenarioBOpt1', 'Escenario B (Optimización 1)')}
              </span>
              <span className="text-xs font-mono text-cyan-700 dark:text-cyan-400">{configB.scenario}</span>
            </div>

            {/* Controls */}
            <div className="space-y-3 mt-3 text-xs">
              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.irrigationStrategyLabel', 'Estrategia de Riego')}</label>
                <select
                  value={configB.irrigationStrategy}
                  onChange={(e) => handleUpdateConfigB({ irrigationStrategy: e.target.value as IrrigationStrategy })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="rainfed">{t('whatIfStudio.optRainfed', 'Secano Estricto')}</option>
                  <option value="deficit_50">{t('whatIfStudio.optDeficit50', 'Riego Deficitario (50% ETc)')}</option>
                  <option value="optimal_100">{t('whatIfStudio.optOptimal100', 'Riego Óptimo (100% ETc)')}</option>
                  <option value="smart_sensor">{t('whatIfStudio.optSmartSensor', 'Sensor Inteligente (VT-R1)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.maizeVarietyLabel', 'Variedad de Maíz')}</label>
                <select
                  value={configB.maizeVariety}
                  onChange={(e) => handleUpdateConfigB({ maizeVariety: e.target.value as MaizeVariety })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="short_cycle">{t('whatIfStudio.optShortCycle', 'Ciclo Corto (90-100d)')}</option>
                  <option value="medium_cycle">{t('whatIfStudio.optMediumCycle', 'Ciclo Medio (110-120d)')}</option>
                  <option value="long_cycle">{t('whatIfStudio.optLongCycle', 'Ciclo Largo (130-140d)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.climateScenarioLabel', 'Escenario Climático CMIP6')}</label>
                <select
                  value={configB.scenario}
                  onChange={(e) => handleUpdateConfigB({ scenario: e.target.value as ClimateScenario })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="SSP1-2.6">{t('whatIfStudio.optSSP1', 'SSP1-2.6 (Optimista)')}</option>
                  <option value="SSP2-4.5">🔵 SSP2-4.5 (Moderado +1.4°C)</option>
                  <option value="SSP3-7.0">{t('whatIfStudio.optSSP3', 'SSP3-7.0 (Intermedio)')}</option>
                  <option value="SSP5-8.5">{t('whatIfStudio.optSSP5', 'SSP5-8.5 (Pesimista)')}</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary Box */}
          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-cyan-500/30 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.yieldLabel', 'Rendimiento:')}</span>
              <strong className="text-cyan-700 dark:text-cyan-300 font-mono text-sm">
                {resultB.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha
                <span className={`text-[11px] ml-1.5 font-bold ${yieldB >= yieldA ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                  ({yieldB >= yieldA ? '+' : ''}{(yieldB - yieldA).toLocaleString()} kg)
                </span>
              </strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.waterConsumedLabel', 'Agua Consumida:')}</span>
              <strong className="text-cyan-700 dark:text-cyan-300 font-mono">
                {resultB.summaryKPIs.totalWaterConsumedMm} mm
                <span className="text-[11px] ml-1.5 text-slate-500 font-normal">
                  ({waterB >= waterA ? '+' : ''}{waterB - waterA} mm)
                </span>
              </strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">Eficiencia Agua (WUE):</span>
              <strong className="text-cyan-800 dark:text-cyan-300 font-mono">{wueB} kg/m³</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.cwsiMaxLabel', 'Estrés Máximo CWSI:')}</span>
              <strong className="text-amber-600 dark:text-amber-400 font-mono">{resultB.summaryKPIs.peakWaterStressIndex.toFixed(2)}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.marginLabel', 'Margen Neto Est.:')}</span>
              <strong className="text-emerald-600 dark:text-emerald-400 font-mono">
                ${resultB.summaryKPIs.economicReturnUsdHa} /ha
                <span className={`text-[11px] ml-1 font-bold ${marginB >= marginA ? 'text-emerald-500' : 'text-rose-500'}`}>
                  ({marginB >= marginA ? '+' : ''}${marginB - marginA})
                </span>
              </strong>
            </div>
          </div>
        </div>

        {/* Scenario C: Sensor + Resilience */}
        <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/80 border border-emerald-500/40 flex flex-col justify-between space-y-4 hover:border-emerald-500/70 transition-all">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
              <span className="px-2.5 py-0.5 rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 font-bold text-xs flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                {t('whatIfStudio.scenarioCSensorRes', 'Escenario C (Sensor + Resiliencia)')}
              </span>
              <span className="text-xs font-mono text-emerald-700 dark:text-emerald-400">{configC.scenario}</span>
            </div>

            {/* Controls */}
            <div className="space-y-3 mt-3 text-xs">
              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.irrigationStrategyLabel', 'Estrategia de Riego')}</label>
                <select
                  value={configC.irrigationStrategy}
                  onChange={(e) => handleUpdateConfigC({ irrigationStrategy: e.target.value as IrrigationStrategy })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="rainfed">{t('whatIfStudio.optRainfed', 'Secano Estricto')}</option>
                  <option value="deficit_50">{t('whatIfStudio.optDeficit50', 'Riego Deficitario (50% ETc)')}</option>
                  <option value="optimal_100">{t('whatIfStudio.optOptimal100', 'Riego Óptimo (100% ETc)')}</option>
                  <option value="smart_sensor">{t('whatIfStudio.optSmartSensor', 'Sensor Inteligente (VT-R1)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.maizeVarietyLabel', 'Variedad de Maíz')}</label>
                <select
                  value={configC.maizeVariety}
                  onChange={(e) => handleUpdateConfigC({ maizeVariety: e.target.value as MaizeVariety })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="short_cycle">{t('whatIfStudio.optShortCycle', 'Ciclo Corto (90-100d)')}</option>
                  <option value="medium_cycle">{t('whatIfStudio.optMediumCycle', 'Ciclo Medio (110-120d)')}</option>
                  <option value="long_cycle">{t('whatIfStudio.optLongCycle', 'Ciclo Largo (130-140d)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1">{t('whatIfStudio.climateScenarioLabel', 'Escenario Climático CMIP6')}</label>
                <select
                  value={configC.scenario}
                  onChange={(e) => handleUpdateConfigC({ scenario: e.target.value as ClimateScenario })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value="SSP1-2.6">{t('whatIfStudio.optSSP1', 'SSP1-2.6 (Optimista)')}</option>
                  <option value="SSP2-4.5">🔵 SSP2-4.5 (Moderado +1.4°C)</option>
                  <option value="SSP3-7.0">{t('whatIfStudio.optSSP3', 'SSP3-7.0 (Intermedio)')}</option>
                  <option value="SSP5-8.5">{t('whatIfStudio.optSSP5', 'SSP5-8.5 (Pesimista)')}</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary Box */}
          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-emerald-500/30 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.yieldLabel', 'Rendimiento:')}</span>
              <strong className="text-emerald-700 dark:text-emerald-300 font-mono text-sm">
                {resultC.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha
                <span className={`text-[11px] ml-1.5 font-bold ${yieldC >= yieldA ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                  ({yieldC >= yieldA ? '+' : ''}{(yieldC - yieldA).toLocaleString()} kg)
                </span>
              </strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.waterConsumedLabel', 'Agua Consumida:')}</span>
              <strong className="text-cyan-700 dark:text-cyan-300 font-mono">
                {resultC.summaryKPIs.totalWaterConsumedMm} mm
                <span className="text-[11px] ml-1.5 text-slate-500 font-normal">
                  ({waterC >= waterA ? '+' : ''}{waterC - waterA} mm)
                </span>
              </strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">Eficiencia Agua (WUE):</span>
              <strong className="text-emerald-700 dark:text-emerald-300 font-mono">{wueC} kg/m³</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.cwsiMaxLabel', 'Estrés Máximo CWSI:')}</span>
              <strong className="text-emerald-600 dark:text-emerald-400 font-mono">{resultC.summaryKPIs.peakWaterStressIndex.toFixed(2)}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 dark:text-slate-400">{t('whatIfStudio.marginLabel', 'Margen Neto Est.:')}</span>
              <strong className="text-emerald-600 dark:text-emerald-400 font-mono">
                ${resultC.summaryKPIs.economicReturnUsdHa} /ha
                <span className={`text-[11px] ml-1 font-bold ${marginC >= marginA ? 'text-emerald-500' : 'text-rose-500'}`}>
                  ({marginC >= marginA ? '+' : ''}${marginC - marginA})
                </span>
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* DEDICATED COMPARISON MATRIX & AGRONOMIC VERDICT */}
      <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Scale className="w-5 h-5 text-teal-600 dark:text-teal-400" />
            Matriz de Comparativa Agronómica & Veredicto PINN
          </h3>
          <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 font-mono">
            Contraste Relativo vs Línea Base (A)
          </span>
        </div>

        {/* Executive Verdict Banner */}
        <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-500/10 via-teal-500/5 to-cyan-500/10 border border-emerald-500/30 shadow-md space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-amber-400/20 text-amber-500 border border-amber-400/30">
                <Trophy className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-700 dark:text-emerald-300">
                  Estrategia Agronómica Recomendada por PINN
                </span>
                <h4 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100">
                  {winnerTitle}
                </h4>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-xl bg-emerald-600 text-white font-mono text-xs font-bold shadow-xs">
                {deltaYieldVsBase >= 0 ? `+${deltaYieldVsBase.toLocaleString()} kg/ha` : `${deltaYieldVsBase.toLocaleString()} kg/ha`} ({deltaYieldPct}%)
              </span>
              <span className="px-3 py-1 rounded-xl bg-cyan-600 text-white font-mono text-xs font-bold shadow-xs">
                {deltaWaterVsBase <= 0 ? `${Math.abs(deltaWaterVsBase)} mm ahorrados` : `+${deltaWaterVsBase} mm agua`}
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
            {winner === 'C' ? (
              <>
                Bajo el forzamiento climático evaluado, el <strong>Escenario C</strong> demuestra la máxima resiliencia agronómica. La adopción de una <strong>variedad de ciclo corto</strong> permite un escape fenológico de sequía antes del pico de evaporación estival, mientras que el <strong>riego de precisión por sensor en floración (VT-R1)</strong> mitiga el estrés hídrico crítico, logrando <strong>{deltaYieldVsBase.toLocaleString()} kg/ha adicionales</strong> con una eficiencia hídrica récord de <strong>{winnerWue} kg/m³</strong> y un margen adicional de <strong>+${deltaMarginVsBase} USD/ha</strong>.
              </>
            ) : winner === 'B' ? (
              <>
                El <strong>Escenario B</strong> equilibra la dotación de agua y la acumulación de biomasa de manera óptima, logrando <strong>{deltaYieldVsBase.toLocaleString()} kg/ha más</strong> que la línea base con una reducción sustancial del costo de bombeo de riego.
              </>
            ) : (
              <>
                La <strong>Línea Base (Escenario A)</strong> mantiene el mayor balance productivo bajo la configuración climática actual sin requerir ajustes en las dosis de riego o ciclo varietal.
              </>
            )}
          </p>
        </div>

        {/* Matrix Comparison Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-xs border-collapse font-sans">
            <thead>
              <tr className="bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800">
                <th className="p-3">Variable Agronómica & KPI</th>
                <th className="p-3">Escenario A (Línea Base)</th>
                <th className="p-3">Escenario B (Optimización 1)</th>
                <th className="p-3">Escenario C (Sensor + Resiliencia)</th>
                <th className="p-3 font-bold text-emerald-600 dark:text-emerald-400">Mejor Opción (Brecha)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-slate-800 dark:text-slate-200">
              {/* Rendimiento */}
              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="p-3 font-sans font-medium text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                  Rendimiento Proyectado
                </td>
                <td className="p-3">{yieldA.toLocaleString()} kg/ha</td>
                <td className="p-3">{yieldB.toLocaleString()} kg/ha</td>
                <td className="p-3">{yieldC.toLocaleString()} kg/ha</td>
                <td className="p-3 font-bold text-emerald-600 dark:text-emerald-400">
                  {winner === 'C' ? `Escenario C (+${(yieldC - yieldA).toLocaleString()} kg)` : winner === 'B' ? `Escenario B (+${(yieldB - yieldA).toLocaleString()} kg)` : 'Línea Base A'}
                </td>
              </tr>

              {/* Productividad del Agua */}
              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="p-3 font-sans font-medium text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <Droplets className="w-3.5 h-3.5 text-cyan-500" />
                  Productividad del Agua (WUE)
                </td>
                <td className="p-3">{wueA} kg/m³</td>
                <td className="p-3">{wueB} kg/m³</td>
                <td className="p-3">{wueC} kg/m³</td>
                <td className="p-3 font-bold text-cyan-600 dark:text-cyan-400">
                  {Number(wueC) >= Number(wueB) && Number(wueC) >= Number(wueA) ? `Escenario C (${wueC} kg/m³)` : Number(wueB) >= Number(wueA) ? `Escenario B (${wueB} kg/m³)` : `Escenario A (${wueA} kg/m³)`}
                </td>
              </tr>

              {/* Agua Total Consumida */}
              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="p-3 font-sans font-medium text-slate-900 dark:text-slate-100">
                  Agua Consumida Total
                </td>
                <td className="p-3">{waterA} mm</td>
                <td className="p-3">{waterB} mm</td>
                <td className="p-3">{waterC} mm</td>
                <td className="p-3 font-semibold text-slate-700 dark:text-slate-300">
                  {Math.min(waterA, waterB, waterC) === waterC ? `Escenario C (${waterC} mm)` : Math.min(waterA, waterB, waterC) === waterB ? `Escenario B (${waterB} mm)` : `Escenario A (${waterA} mm)`}
                </td>
              </tr>

              {/* Estrés Máximo CWSI */}
              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="p-3 font-sans font-medium text-slate-900 dark:text-slate-100">
                  Estrés Hídrico Máximo (CWSI)
                </td>
                <td className="p-3">{cwsiA.toFixed(2)}</td>
                <td className="p-3">{cwsiB.toFixed(2)}</td>
                <td className="p-3">{cwsiC.toFixed(2)}</td>
                <td className="p-3 font-semibold text-emerald-600 dark:text-emerald-400">
                  {Math.min(cwsiA, cwsiB, cwsiC) === cwsiC ? `Escenario C (${cwsiC.toFixed(2)} pico)` : Math.min(cwsiA, cwsiB, cwsiC) === cwsiB ? `Escenario B (${cwsiB.toFixed(2)} pico)` : `Escenario A (${cwsiA.toFixed(2)})`}
                </td>
              </tr>

              {/* Retorno Económico */}
              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="p-3 font-sans font-medium text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-emerald-500" />
                  Margen Neto Económico
                </td>
                <td className="p-3">${marginA.toLocaleString()} /ha</td>
                <td className="p-3">${marginB.toLocaleString()} /ha</td>
                <td className="p-3">${marginC.toLocaleString()} /ha</td>
                <td className="p-3 font-bold text-emerald-600 dark:text-emerald-400">
                  {marginC >= marginB && marginC >= marginA ? `Escenario C (+$${marginC - marginA}/ha)` : marginB >= marginA ? `Escenario B (+$${marginB - marginA}/ha)` : 'Línea Base A'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Visual Bar Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Yield Bar */}
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
            <span className="font-semibold text-slate-700 dark:text-slate-300 block">Comparativa Rendimiento (kg/ha)</span>
            <div className="space-y-1.5 font-mono text-[11px]">
              <div>
                <div className="flex justify-between text-slate-500 mb-0.5">
                  <span>A: {yieldA.toLocaleString()}</span>
                  <span>100%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-slate-500 h-full rounded-full" style={{ width: `${(yieldA / maxYield) * 100}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-cyan-600 dark:text-cyan-400 mb-0.5">
                  <span>B: {yieldB.toLocaleString()}</span>
                  <span>{((yieldB / yieldA) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${(yieldB / maxYield) * 100}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-bold mb-0.5">
                  <span>C: {yieldC.toLocaleString()}</span>
                  <span>{((yieldC / yieldA) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(yieldC / maxYield) * 100}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Water Productivity Bar */}
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
            <span className="font-semibold text-slate-700 dark:text-slate-300 block">Eficiencia Hídrica (kg grano / m³)</span>
            <div className="space-y-1.5 font-mono text-[11px]">
              <div>
                <div className="flex justify-between text-slate-500 mb-0.5">
                  <span>A: {wueA} kg/m³</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-slate-500 h-full rounded-full" style={{ width: `${(Number(wueA) / Math.max(Number(wueA), Number(wueB), Number(wueC))) * 100}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-cyan-600 dark:text-cyan-400 mb-0.5">
                  <span>B: {wueB} kg/m³</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${(Number(wueB) / Math.max(Number(wueA), Number(wueB), Number(wueC))) * 100}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-bold mb-0.5">
                  <span>C: {wueC} kg/m³</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(Number(wueC) / Math.max(Number(wueA), Number(wueB), Number(wueC))) * 100}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Economic Return Bar */}
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
            <span className="font-semibold text-slate-700 dark:text-slate-300 block">Margen Financiero ($ USD/ha)</span>
            <div className="space-y-1.5 font-mono text-[11px]">
              <div>
                <div className="flex justify-between text-slate-500 mb-0.5">
                  <span>A: ${marginA.toLocaleString()}</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-slate-500 h-full rounded-full" style={{ width: `${(marginA / maxMargin) * 100}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-cyan-600 dark:text-cyan-400 mb-0.5">
                  <span>B: ${marginB.toLocaleString()}</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${(marginB / maxMargin) * 100}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-emerald-600 dark:text-emerald-400 font-bold mb-0.5">
                  <span>C: ${marginC.toLocaleString()}</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(marginC / maxMargin) * 100}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
