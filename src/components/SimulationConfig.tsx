import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Play, 
  Cpu, 
  Flame, 
  CloudRain, 
  Calendar, 
  Sliders, 
  Droplets, 
  Sparkles, 
  AlertCircle,
  HelpCircle,
  Clock,
  Zap,
  Info
} from 'lucide-react';
import { 
  ClimateScenario, 
  Field, 
  IrrigationStrategy, 
  MaizeVariety, 
  SimulationConfig 
} from '../types';
import { getCMIP6ClimateForcing } from '../services/pinnEngine';
import { fetchScenarios, fetchSoilProfiles } from '../services/api';

interface SimulationConfigProps {
  field: Field;
  config: SimulationConfig;
  onChangeConfig: (newConfig: SimulationConfig) => void;
  onRunSimulation: () => void;
  isLoading: boolean;
}

export const SimulationConfigPanel: React.FC<SimulationConfigProps> = ({
  field,
  config,
  onChangeConfig,
  onRunSimulation,
  isLoading
}) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'climate' | 'crop' | 'irrigation' | 'soil'>('climate');
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [soilProfiles, setSoilProfiles] = useState<any[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    const loadMasterData = async () => {
      try {
        const [scenariosData, soilData] = await Promise.all([
          fetchScenarios(),
          fetchSoilProfiles()
        ]);
        
        if (!scenariosData.fallback) {
          setScenarios(scenariosData.scenarios);
        }
        if (!soilData.fallback) {
          setSoilProfiles(soilData.soilProfiles);
        }
      } catch (error) {
        console.warn('Failed to load master data, using fallbacks', error);
      } finally {
        setLoadingData(false);
      }
    };
    
    loadMasterData();
  }, []);

  const forcing = getCMIP6ClimateForcing(config.scenario, config.targetYear);

  const handleScenarioChange = (scenario: ClimateScenario) => {
    onChangeConfig({ ...config, scenario });
  };

  const handleYearChange = (targetYear: number) => {
    onChangeConfig({ ...config, targetYear });
  };

  const handleVarietyChange = (maizeVariety: MaizeVariety) => {
    onChangeConfig({ ...config, maizeVariety });
  };

  const handleIrrigationChange = (irrigationStrategy: IrrigationStrategy) => {
    onChangeConfig({ ...config, irrigationStrategy });
  };

  return (
    <div id="simulation-config-panel" className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            Configuración de Simulación & Forzamiento PINN
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Parámetros climáticos CMIP6, fenología varietal y balance hídrico Richards para <strong className="text-slate-800 dark:text-slate-200">{field.name}</strong>.
          </p>
        </div>

        <button
          id="btn-execute-simulation"
          onClick={onRunSimulation}
          disabled={isLoading}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:scale-95 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>{t('simConfig.executeLoading')}</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 text-amber-300" />
              <span>{t('simConfig.executeButton')}</span>
            </>
          )}
        </button>
      </div>

      {/* Navigation Pills */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-50 dark:bg-slate-950/80 rounded-xl border border-slate-200/80 dark:border-slate-800/80 overflow-x-auto">
        <button
          onClick={() => setActiveTab('climate')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
            activeTab === 'climate' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Flame className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
          Escenarios Climáticos CMIP6
        </button>
        <button
          onClick={() => setActiveTab('crop')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
            activeTab === 'crop' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Calendar className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          Variedad & Calendario
        </button>
        <button
          onClick={() => setActiveTab('irrigation')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
            activeTab === 'irrigation' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Droplets className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
          {t('simulationConfig.tabIrrigation')}
        </button>
        <button
          onClick={() => setActiveTab('soil')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
            activeTab === 'soil' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Cpu className="w-3.5 h-3.5 text-violet-600 dark:text-violet-400" />
          Suelo & Condiciones Iniciales
        </button>
      </div>

      {/* Tab 1: Climate Scenarios */}
      {activeTab === 'climate' && (
        <div className="space-y-4">
          {loadingData ? (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 text-center text-xs text-slate-600 dark:text-slate-400">
              Cargando escenarios climáticos del backend...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {scenarios.length > 0 ? scenarios.map((scenario: any) => (
                <div
                  key={scenario.id}
                  onClick={() => handleScenarioChange(scenario.id as ClimateScenario)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    config.scenario === scenario.id
                      ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 ring-1 ring-emerald-500/50'
                      : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`px-2 py-0.5 rounded-md font-bold text-[11px] ${
                      scenario.risk === 'low' ? 'bg-emerald-500/20 text-emerald-800 dark:text-emerald-300' :
                      scenario.risk === 'medium' ? 'bg-amber-500/20 text-amber-800 dark:text-amber-300' :
                      'bg-rose-500/20 text-rose-800 dark:text-rose-300'
                    }`}>
                      {scenario.label}
                    </span>
                    <span className={`text-[11px] font-mono ${
                      scenario.risk === 'low' ? 'text-emerald-600 dark:text-emerald-400' :
                      scenario.risk === 'medium' ? 'text-amber-600 dark:text-amber-400' :
                      'text-rose-600 dark:text-rose-400'
                    }`}>
                      {scenario.risk === 'low' ? 'Bajo' : scenario.risk === 'medium' ? 'Medio' : 'Alto'} Riesgo
                    </span>
                  </div>
                  <p className="text-xs text-slate-800 dark:text-slate-300">Escenario CMIP6 {scenario.id}</p>
                  <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
                    Anomalía térmica local: <span className="font-mono text-emerald-700 dark:text-emerald-300">+{forcing.tempAnomalyC.toFixed(1)}°C</span>
                  </div>
                </div>
              )) : (
                <>
                  {/* Fallback scenarios hardcoded */}
                  <div
                    onClick={() => handleScenarioChange('SSP1-2.6')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      config.scenario === 'SSP1-2.6'
                        ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 ring-1 ring-emerald-500/50'
                        : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 font-bold text-[11px]">
                        Optimista (SSP1-2.6)
                      </span>
                      <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-mono">+1.5°C Global</span>
                    </div>
                    <p className="text-xs text-slate-800 dark:text-slate-300">{t('simConfig.scenarioSustainable')}</p>
                    <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
                      Anomalía térmica local: <span className="font-mono text-emerald-700 dark:text-emerald-300">+{forcing.tempAnomalyC.toFixed(1)}°C</span>
                    </div>
                  </div>

                  <div
                    onClick={() => handleScenarioChange('SSP3-7.0')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      config.scenario === 'SSP3-7.0'
                        ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-500 ring-1 ring-amber-500/50'
                        : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-800 dark:text-amber-300 font-bold text-[11px]">
                        Intermedio (SSP3-7.0)
                      </span>
                      <span className="text-[11px] text-amber-600 dark:text-amber-400 font-mono">+2.7°C Global</span>
                    </div>
                    <p className="text-xs text-slate-800 dark:text-slate-300">{t('simConfig.scenarioRivalry')}</p>
                    <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
                      Anomalía térmica local: <span className="font-mono text-amber-700 dark:text-amber-300">+{forcing.tempAnomalyC.toFixed(1)}°C</span>
                    </div>
                  </div>

                  <div
                    onClick={() => handleScenarioChange('SSP5-8.5')}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      config.scenario === 'SSP5-8.5'
                        ? 'bg-rose-50 dark:bg-rose-950/40 border-rose-500 ring-1 ring-rose-500/50'
                        : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-800 dark:text-rose-300 font-bold text-[11px]">
                        Pesimista (SSP5-8.5)
                      </span>
                      <span className="text-[11px] text-rose-600 dark:text-rose-400 font-mono">+4.4°C Global</span>
                    </div>
                    <p className="text-xs text-slate-800 dark:text-slate-300">{t('simConfig.scenarioFossil')}</p>
                    <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400">
                      Anomalía térmica local: <span className="font-mono text-rose-700 dark:text-rose-300">+{forcing.tempAnomalyC.toFixed(1)}°C</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Target Year Timeline Slider */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-800 dark:text-slate-300 font-semibold flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                Horizonte Temporal de Proyección (2026 - 2050)
              </span>
              <span className="px-2.5 py-0.5 rounded-md bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 font-mono font-bold">
                Año {config.targetYear}
              </span>
            </div>
            <input
              type="range"
              min={2026}
              max={2050}
              step={1}
              value={config.targetYear}
              onChange={(e) => handleYearChange(parseInt(e.target.value, 10))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <div className="flex justify-between text-[11px] font-mono text-slate-500">
              <span>2026 (Presente)</span>
              <span>2035 (Medio Plazo)</span>
              <span>2050 (Horizonte IPCC)</span>
            </div>
          </div>

          {/* Climatological Forcing Parameters Summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 text-[11px] block">{t('simConfig.atmosphericCo2')}</span>
              <strong className="text-slate-800 dark:text-slate-200 font-mono">{Math.round(forcing.co2Ppm)} ppm</strong>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 text-[11px] block">{t('simConfig.thermalAnomaly')}</span>
              <strong className="text-amber-600 dark:text-amber-400 font-mono">+{forcing.tempAnomalyC.toFixed(2)} °C</strong>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 text-[11px] block">{t('simConfig.precipModifier')}</span>
              <strong className="text-cyan-600 dark:text-cyan-400 font-mono">{Math.round(forcing.precipMultiplier * 100)}% de normal</strong>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 text-[11px] block">{t('simConfig.heatwaveRisk')}</span>
              <strong className="text-rose-600 dark:text-rose-400 font-mono">{Math.round(forcing.heatwaveFrequencyRisk * 100)}% prob/semana</strong>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Crop Variety & Planting Date */}
      {activeTab === 'crop' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Short Cycle */}
            <div
              onClick={() => handleVarietyChange('short_cycle')}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                config.maizeVariety === 'short_cycle'
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 ring-1 ring-emerald-500/50'
                  : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
              }`}
            >
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('simConfig.cycleShort')}</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                Variedad precoz para escapar de la sequía tardía. Menor requerimiento de GDD (1450 °C·d).
              </p>
              <div className="mt-3 text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
                Potencial: 10,500 kg/ha
              </div>
            </div>

            {/* Medium Cycle */}
            <div
              onClick={() => handleVarietyChange('medium_cycle')}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                config.maizeVariety === 'medium_cycle'
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 ring-1 ring-emerald-500/50'
                  : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
              }`}
            >
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('simConfig.cycleMedium')}</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                Balance óptimo entre biomasa acumulada y escape a estrés hídrico (1750 °C·d).
              </p>
              <div className="mt-3 text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
                Potencial: 13,500 kg/ha
              </div>
            </div>

            {/* Long Cycle */}
            <div
              onClick={() => handleVarietyChange('long_cycle')}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                config.maizeVariety === 'long_cycle'
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 ring-1 ring-emerald-500/50'
                  : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
              }`}
            >
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('simConfig.cycleLong')}</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                Máximo rendimiento potencial en condiciones de alta disponibilidad hídrica (2050 °C·d).
              </p>
              <div className="mt-3 text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
                Potencial: 16,000 kg/ha
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
              <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1.5 font-medium">
                Fecha de Siembra Programada
              </label>
              <input
                type="date"
                value={config.plantingDate}
                onChange={(e) => onChangeConfig({ ...config, plantingDate: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-mono text-xs focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
              <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1.5 font-medium">
                Fertilización Nitrogenada (kg N / ha)
              </label>
              <input
                type="number"
                min={0}
                max={350}
                value={config.nitrogenApplicationKgHa}
                onChange={(e) => onChangeConfig({ ...config, nitrogenApplicationKgHa: parseInt(e.target.value, 10) || 0 })}
                className="w-full px-3 py-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-mono text-xs focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Irrigation Strategy */}
      {activeTab === 'irrigation' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Rainfed */}
            <div
              onClick={() => handleIrrigationChange('rainfed')}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                config.irrigationStrategy === 'rainfed'
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 ring-1 ring-emerald-500/50'
                  : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
              }`}
            >
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">{t('simConfig.irrigationRainfed')}</h4>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1">{t('simConfig.irrigationRainfedDesc')}</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-[10px] text-slate-800 dark:text-slate-300">0 mm Riego</span>
            </div>

            {/* Deficit 50% */}
            <div
              onClick={() => handleIrrigationChange('deficit_50')}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                config.irrigationStrategy === 'deficit_50'
                  ? 'bg-cyan-50 dark:bg-cyan-950/40 border-cyan-500 ring-1 ring-cyan-500/50'
                  : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
              }`}
            >
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">{t('simConfig.irrigationDeficit')}</h4>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1">{t('simConfig.irrigationDeficitDesc')}</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded bg-cyan-100 dark:bg-cyan-950 text-cyan-800 dark:text-cyan-300 text-[10px]">{t('simConfig.waterSavings')}</span>
            </div>

            {/* Optimal 100% */}
            <div
              onClick={() => handleIrrigationChange('optimal_100')}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                config.irrigationStrategy === 'optimal_100'
                  ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-500 ring-1 ring-blue-500/50'
                  : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
              }`}
            >
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">{t('simConfig.irrigationOptimal')}</h4>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1">{t('simConfig.irrigationOptimalDesc')}</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 text-[10px]">{t('simConfig.maxBiomass')}</span>
            </div>

            {/* Smart Sensor Triggered */}
            <div
              onClick={() => handleIrrigationChange('smart_sensor')}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                config.irrigationStrategy === 'smart_sensor'
                  ? 'bg-violet-50 dark:bg-violet-950/40 border-violet-500 ring-1 ring-violet-500/50'
                  : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
              }`}
            >
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-violet-600 dark:text-violet-400" />
                {t('simulationConfig.smartSensor')}
              </h4>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1">Prioriza riego en floración para proteger el índice de cosecha.</p>
              <span className="mt-2 inline-block px-2 py-0.5 rounded bg-violet-100 dark:bg-violet-950 text-violet-800 dark:text-violet-300 text-[10px]">{t('simConfig.maxEfficiency')}</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Soil & Initial Moisture */}
      {activeTab === 'soil' && (
        <div className="space-y-4">
          {loadingData ? (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 text-center text-xs text-slate-600 dark:text-slate-400">
              Cargando perfiles de suelo del backend...
            </div>
          ) : (
            <>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-800 dark:text-slate-300 font-semibold">
                    Perfil de Suelo Actual
                  </span>
                  <span className="font-mono text-cyan-600 dark:text-cyan-400 font-bold">
                    {field.soilProfile.label}
                  </span>
                </div>
                
                {soilProfiles.length > 0 && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {soilProfiles.map((profile: any) => (
                      <div
                        key={profile.id}
                        className={`p-2 rounded-lg border cursor-pointer transition-all ${
                          field.soilProfile.type === profile.id
                            ? 'bg-cyan-50 dark:bg-cyan-950/40 border-cyan-500'
                            : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600'
                        }`}
                        onClick={() => {
                          // Update field soil profile (this would need to be handled by parent)
                          console.log('Selected soil profile:', profile.id);
                        }}
                      >
                        <div className="text-[11px] font-semibold text-slate-800 dark:text-slate-200">{profile.label}</div>
                        <div className="text-[10px] text-slate-600 dark:text-slate-400 mt-0.5">
                          FC: {profile.fieldCapacity} | WP: {profile.wiltingPoint}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-800 dark:text-slate-300 font-semibold">
                    Humedad Inicial del Perfil (% de Capacidad de Agua Disponible)
                  </span>
                  <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                    {config.soilMoistureInitialPercent}% AWC
                  </span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={100}
                  step={5}
                  value={config.soilMoistureInitialPercent}
                  onChange={(e) => onChangeConfig({ ...config, soilMoistureInitialPercent: parseInt(e.target.value, 10) || 50 })}
                  className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>{t('simConfig.soilDry')}</span>
                  <span>{t('simConfig.soilModerate')}</span>
                  <span>{t('simConfig.fieldCapacity')}</span>
                </div>
              </div>
            </>
          )}

          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs flex items-start gap-3">
            <Info className="w-4 h-4 text-cyan-600 dark:text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="text-slate-800 dark:text-slate-300">
              El motor de Physics-Informed Neural Network (PINN) calcula el tensor de flujo 1D de Richards con K(h) según la curva de retención de Van Genuchten del suelo <strong>{field.soilProfile.label}</strong> (α = {field.soilProfile.alphaVanGenuchten}, n = {field.soilProfile.nVanGenuchten}).
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
