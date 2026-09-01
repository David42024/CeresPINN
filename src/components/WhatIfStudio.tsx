import React, { useState, useEffect } from 'react';
import { 
  GitCompare, 
  Sparkles, 
  TrendingUp, 
  Droplets, 
  DollarSign, 
  ShieldCheck, 
  Sliders, 
  ArrowRight, 
  Calendar,
  Layers,
  Zap
} from 'lucide-react';
import { 
  Field, 
  SimulationConfig, 
  SimulationResult, 
  ClimateScenario, 
  IrrigationStrategy, 
  MaizeVariety 
} from '../types';
import { runPINNSimulation } from '../services/pinnEngine';
import { simulateScenario } from '../services/api';

interface WhatIfStudioProps {
  field: Field;
  baseConfig: SimulationConfig;
}

export const WhatIfStudio: React.FC<WhatIfStudioProps> = ({ field, baseConfig }) => {
  // Scenario 1 (Baseline)
  const [configA, setConfigA] = useState<SimulationConfig>({ ...baseConfig });
  const [resultA, setResultA] = useState<SimulationResult>(() => runPINNSimulation(field, baseConfig));

  // Scenario 2 (Optimization 1 - Deficit or Date shift)
  const [configB, setConfigB] = useState<SimulationConfig>({
    ...baseConfig,
    irrigationStrategy: 'deficit_50',
    maizeVariety: 'medium_cycle'
  });
  const [resultB, setResultB] = useState<SimulationResult>(() => 
    runPINNSimulation(field, { ...baseConfig, irrigationStrategy: 'deficit_50', maizeVariety: 'medium_cycle' })
  );

  // Scenario 3 (Optimization 2 - Sensor + Short cycle drought escape)
  const [configC, setConfigC] = useState<SimulationConfig>({
    ...baseConfig,
    irrigationStrategy: 'smart_sensor',
    maizeVariety: 'short_cycle'
  });
  const [resultC, setResultC] = useState<SimulationResult>(() => 
    runPINNSimulation(field, { ...baseConfig, irrigationStrategy: 'smart_sensor', maizeVariety: 'short_cycle' })
  );

  // Re-run when configs change
  const refreshScenario = async (setter: React.Dispatch<React.SetStateAction<SimulationConfig>>, resultSetter: React.Dispatch<React.SetStateAction<SimulationResult>>, updated: SimulationConfig) => {
    setter(updated);
    try {
      const result = await simulateScenario(field, updated);
      resultSetter(result);
    } catch (error) {
      console.error('Failed to resolve scenario via backend', error);
      resultSetter(runPINNSimulation(field, updated));
    }
  };

  const handleUpdateConfigA = (updates: Partial<SimulationConfig>) => {
    const updated = { ...configA, ...updates };
    void refreshScenario(setConfigA, setResultA, updated);
  };

  const handleUpdateConfigB = (updates: Partial<SimulationConfig>) => {
    const updated = { ...configB, ...updates };
    void refreshScenario(setConfigB, setResultB, updated);
  };

  const handleUpdateConfigC = (updates: Partial<SimulationConfig>) => {
    const updated = { ...configC, ...updates };
    void refreshScenario(setConfigC, setResultC, updated);
  };

  return (
    <div id="what-if-analysis-studio" className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-emerald-400" />
            Módulo de Análisis Comparativo "¿Qué pasa si?" (What-If Studio)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Evalúa y contrasta 3 estrategias agronómicas simultáneas bajo forzamiento climático PINN.
          </p>
        </div>

        <div className="px-3 py-1 rounded-xl bg-emerald-950/70 border border-emerald-700/50 text-emerald-300 text-xs font-mono flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          Inferencia PINN en Tiempo Real
        </div>
      </div>

      {/* 3 Columns: Side-by-Side Scenario Configuration & Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Scenario A */}
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="px-2.5 py-0.5 rounded-lg bg-slate-800 text-slate-200 font-bold text-xs">
                Escenario A (Línea Base)
              </span>
              <span className="text-xs font-mono text-slate-400">{configA.scenario}</span>
            </div>

            {/* Controls */}
            <div className="space-y-3 mt-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Estrategia de Riego</label>
                <select
                  value={configA.irrigationStrategy}
                  onChange={(e) => handleUpdateConfigA({ irrigationStrategy: e.target.value as IrrigationStrategy })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="rainfed">Secano Estricto</option>
                  <option value="deficit_50">Riego Deficitario (50% ETc)</option>
                  <option value="optimal_100">Riego Óptimo (100% ETc)</option>
                  <option value="smart_sensor">Sensor Inteligente (VT-R1)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Variedad de Maíz</label>
                <select
                  value={configA.maizeVariety}
                  onChange={(e) => handleUpdateConfigA({ maizeVariety: e.target.value as MaizeVariety })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="short_cycle">Ciclo Corto (90-100d)</option>
                  <option value="medium_cycle">Ciclo Medio (110-120d)</option>
                  <option value="long_cycle">Ciclo Largo (130-140d)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Escenario Climático CMIP6</label>
                <select
                  value={configA.scenario}
                  onChange={(e) => handleUpdateConfigA({ scenario: e.target.value as ClimateScenario })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="SSP1-2.6">SSP1-2.6 (Optimista)</option>
                  <option value="SSP3-7.0">SSP3-7.0 (Intermedio)</option>
                  <option value="SSP5-8.5">SSP5-8.5 (Pesimista)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary Box */}
          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Rendimiento:</span>
              <strong className="text-slate-100 font-mono text-sm">{resultA.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Agua Consumida:</span>
              <strong className="text-cyan-300 font-mono">{resultA.summaryKPIs.totalWaterConsumedMm} mm</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Estrés Máximo CWSI:</span>
              <strong className="text-amber-400 font-mono">{resultA.summaryKPIs.peakWaterStressIndex.toFixed(2)}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Margen Neto Est.:</span>
              <strong className="text-emerald-400 font-mono">${resultA.summaryKPIs.economicReturnUsdHa} /ha</strong>
            </div>
          </div>
        </div>

        {/* Scenario B */}
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-cyan-500/40 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold text-xs">
                Escenario B (Optimización 1)
              </span>
              <span className="text-xs font-mono text-cyan-400">{configB.scenario}</span>
            </div>

            {/* Controls */}
            <div className="space-y-3 mt-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Estrategia de Riego</label>
                <select
                  value={configB.irrigationStrategy}
                  onChange={(e) => handleUpdateConfigB({ irrigationStrategy: e.target.value as IrrigationStrategy })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="rainfed">Secano Estricto</option>
                  <option value="deficit_50">Riego Deficitario (50% ETc)</option>
                  <option value="optimal_100">Riego Óptimo (100% ETc)</option>
                  <option value="smart_sensor">Sensor Inteligente (VT-R1)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Variedad de Maíz</label>
                <select
                  value={configB.maizeVariety}
                  onChange={(e) => handleUpdateConfigB({ maizeVariety: e.target.value as MaizeVariety })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="short_cycle">Ciclo Corto (90-100d)</option>
                  <option value="medium_cycle">Ciclo Medio (110-120d)</option>
                  <option value="long_cycle">Ciclo Largo (130-140d)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Escenario Climático CMIP6</label>
                <select
                  value={configB.scenario}
                  onChange={(e) => handleUpdateConfigB({ scenario: e.target.value as ClimateScenario })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="SSP1-2.6">SSP1-2.6 (Optimista)</option>
                  <option value="SSP3-7.0">SSP3-7.0 (Intermedio)</option>
                  <option value="SSP5-8.5">SSP5-8.5 (Pesimista)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary Box */}
          <div className="p-3.5 rounded-xl bg-slate-900 border border-cyan-500/30 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Rendimiento:</span>
              <strong className="text-cyan-300 font-mono text-sm">
                {resultB.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha
                <span className="text-[11px] ml-1.5 text-emerald-400">
                  ({resultB.summaryKPIs.projectedYieldKgHa >= resultA.summaryKPIs.projectedYieldKgHa ? '+' : ''}
                  {resultB.summaryKPIs.projectedYieldKgHa - resultA.summaryKPIs.projectedYieldKgHa} kg)
                </span>
              </strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Agua Consumida:</span>
              <strong className="text-cyan-300 font-mono">{resultB.summaryKPIs.totalWaterConsumedMm} mm</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Estrés Máximo CWSI:</span>
              <strong className="text-amber-400 font-mono">{resultB.summaryKPIs.peakWaterStressIndex.toFixed(2)}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Margen Neto Est.:</span>
              <strong className="text-emerald-400 font-mono">${resultB.summaryKPIs.economicReturnUsdHa} /ha</strong>
            </div>
          </div>
        </div>

        {/* Scenario C */}
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-emerald-500/40 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="px-2.5 py-0.5 rounded-lg bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold text-xs">
                Escenario C (Sensor + Resiliencia)
              </span>
              <span className="text-xs font-mono text-emerald-400">{configC.scenario}</span>
            </div>

            {/* Controls */}
            <div className="space-y-3 mt-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Estrategia de Riego</label>
                <select
                  value={configC.irrigationStrategy}
                  onChange={(e) => handleUpdateConfigC({ irrigationStrategy: e.target.value as IrrigationStrategy })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="rainfed">Secano Estricto</option>
                  <option value="deficit_50">Riego Deficitario (50% ETc)</option>
                  <option value="optimal_100">Riego Óptimo (100% ETc)</option>
                  <option value="smart_sensor">Sensor Inteligente (VT-R1)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Variedad de Maíz</label>
                <select
                  value={configC.maizeVariety}
                  onChange={(e) => handleUpdateConfigC({ maizeVariety: e.target.value as MaizeVariety })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="short_cycle">Ciclo Corto (90-100d)</option>
                  <option value="medium_cycle">Ciclo Medio (110-120d)</option>
                  <option value="long_cycle">Ciclo Largo (130-140d)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Escenario Climático CMIP6</label>
                <select
                  value={configC.scenario}
                  onChange={(e) => handleUpdateConfigC({ scenario: e.target.value as ClimateScenario })}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value="SSP1-2.6">SSP1-2.6 (Optimista)</option>
                  <option value="SSP3-7.0">SSP3-7.0 (Intermedio)</option>
                  <option value="SSP5-8.5">SSP5-8.5 (Pesimista)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary Box */}
          <div className="p-3.5 rounded-xl bg-slate-900 border border-emerald-500/30 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Rendimiento:</span>
              <strong className="text-emerald-300 font-mono text-sm">
                {resultC.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha
                <span className="text-[11px] ml-1.5 text-emerald-400">
                  ({resultC.summaryKPIs.projectedYieldKgHa >= resultA.summaryKPIs.projectedYieldKgHa ? '+' : ''}
                  {resultC.summaryKPIs.projectedYieldKgHa - resultA.summaryKPIs.projectedYieldKgHa} kg)
                </span>
              </strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Agua Consumida:</span>
              <strong className="text-cyan-300 font-mono">{resultC.summaryKPIs.totalWaterConsumedMm} mm</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Estrés Máximo CWSI:</span>
              <strong className="text-emerald-400 font-mono">{resultC.summaryKPIs.peakWaterStressIndex.toFixed(2)}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Margen Neto Est.:</span>
              <strong className="text-emerald-400 font-mono">${resultC.summaryKPIs.economicReturnUsdHa} /ha</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
