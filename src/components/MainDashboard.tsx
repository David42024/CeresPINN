import React, { useState } from 'react';
import { 
  TrendingUp, 
  Droplets, 
  Activity, 
  AlertTriangle, 
  ShieldAlert, 
  DollarSign, 
  Calendar, 
  BarChart3, 
  Layers, 
  Maximize2, 
  ChevronRight,
  Info,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  CartesianGrid, 
  ReferenceLine 
} from 'recharts';
import { SimulationResult } from '../types';

interface MainDashboardProps {
  simulation: SimulationResult;
  currentDayIndex: number;
  onSelectDayIndex: (idx: number) => void;
}

type ChartView = 'soil_layers' | 'biomass_lai' | 'water_fluxes' | 'stress_cwsi';

export const MainDashboard: React.FC<MainDashboardProps> = ({
  simulation,
  currentDayIndex,
  onSelectDayIndex
}) => {
  const [activeChartView, setActiveChartView] = useState<ChartView>('soil_layers');
  const kpi = simulation.summaryKPIs;
  const currentDay = simulation.dailyRecords[currentDayIndex] || simulation.dailyRecords[0];

  return (
    <div id="main-dashboard-container" className="space-y-5">
      {/* 4 Major KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Projected Yield */}
        <div id="kpi-projected-yield" className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden group hover:border-emerald-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Rendimiento Proyectado</span>
            <div className="p-2 rounded-xl bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono tracking-tight">
              {kpi.projectedYieldKgHa.toLocaleString()}
            </span>
            <span className="text-xs text-slate-400 font-mono">kg/ha</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
            <span className="text-slate-500">Potencial: {(kpi.potentialYieldKgHa / 1000).toFixed(1)} t/ha</span>
            <span className={`font-semibold flex items-center ${
              kpi.yieldLossDueToDroughtPercent > 20 ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {kpi.yieldLossDueToDroughtPercent > 20 ? <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" /> : <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />}
              {kpi.yieldLossDueToDroughtPercent > 0 ? `-${kpi.yieldLossDueToDroughtPercent}%` : 'Óptimo'}
            </span>
          </div>
        </div>

        {/* KPI 2: Water Stress Index */}
        <div id="kpi-water-stress" className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden group hover:border-amber-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Índice Estrés CWSI</span>
            <div className="p-2 rounded-xl bg-amber-950/80 text-amber-400 border border-amber-800/60">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono tracking-tight">
              {kpi.peakWaterStressIndex.toFixed(2)}
            </span>
            <span className="text-xs text-slate-400 font-mono">Pico (0-1)</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
            <span className="text-slate-500">Días Críticos: {kpi.criticalDroughtDaysCount} d</span>
            <span className="text-amber-400 font-semibold">Promedio: {kpi.avgWaterStressIndex}</span>
          </div>
        </div>

        {/* KPI 3: Biomass & Canopy */}
        <div id="kpi-biomass" className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden group hover:border-cyan-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Biomasa Acumulada</span>
            <div className="p-2 rounded-xl bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono tracking-tight">
              {(kpi.totalBiomassKgHa / 1000).toFixed(1)}
            </span>
            <span className="text-xs text-slate-400 font-mono">t/ha materia seca</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
            <span className="text-slate-500">Días a Madurez</span>
            <span className="text-cyan-300 font-mono font-semibold">{kpi.daysToMaturity} días</span>
          </div>
        </div>

        {/* KPI 4: Water Productivity */}
        <div id="kpi-water-productivity" className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden group hover:border-violet-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Productividad del Agua</span>
            <div className="p-2 rounded-xl bg-violet-950/80 text-violet-400 border border-violet-800/60">
              <Droplets className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-100 font-mono tracking-tight">
              {kpi.waterProductivityKgM3.toFixed(2)}
            </span>
            <span className="text-xs text-slate-400 font-mono">kg grano / m³</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
            <span className="text-slate-500">Agua Total Consumida</span>
            <span className="text-violet-300 font-mono font-semibold">{kpi.totalWaterConsumedMm} mm</span>
          </div>
        </div>
      </div>

      {/* Active Alerts Panel */}
      {simulation.alerts.length > 0 && (
        <div id="active-alerts-section" className="space-y-2">
          {simulation.alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3.5 rounded-2xl border flex items-start gap-3 transition-all ${
                alert.level === 'critical'
                  ? 'bg-rose-950/40 border-rose-800/80 text-rose-200'
                  : 'bg-amber-950/30 border-amber-800/60 text-amber-200'
              }`}
            >
              {alert.level === 'critical' ? (
                <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <h4 className="text-sm font-bold text-slate-100">{alert.title}</h4>
                  <span className="text-[11px] px-2 py-0.5 rounded-md bg-slate-900/80 border border-slate-800 font-mono">
                    {alert.timing}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">{alert.description}</p>
                <div className="mt-2 text-xs font-medium text-emerald-400 flex items-center gap-1">
                  <span>Recomendación agronómica:</span>
                  <span className="text-slate-200">{alert.recommendedAction}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Interactive Time-Series Charts Section */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-4">
        {/* Chart View Switcher */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-400" />
              Dinámica Temporal del Gemelo Digital (Resolución Diaria)
            </h3>
            <p className="text-xs text-slate-400">
              Evolución simulada durante los {simulation.dailyRecords.length} días del ciclo de cultivo.
            </p>
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-slate-950 rounded-xl border border-slate-800 text-xs">
            <button
              id="btn-chart-soil-layers"
              onClick={() => setActiveChartView('soil_layers')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeChartView === 'soil_layers' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Humedad Suelo (3 Capas)
            </button>
            <button
              id="btn-chart-biomass"
              onClick={() => setActiveChartView('biomass_lai')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeChartView === 'biomass_lai' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Biomasa & LAI
            </button>
            <button
              id="btn-chart-water-fluxes"
              onClick={() => setActiveChartView('water_fluxes')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeChartView === 'water_fluxes' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Balance de Agua (ET vs Riego/Lluvia)
            </button>
            <button
              id="btn-chart-stress"
              onClick={() => setActiveChartView('stress_cwsi')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeChartView === 'stress_cwsi' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Estrés CWSI & Térmico
            </button>
          </div>
        </div>

        {/* Chart 1: Soil Moisture 3 Depths */}
        {activeChartView === 'soil_layers' && (
          <div className="h-[320px] w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simulation.dailyRecords} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="dap" stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: 'Días Tras Siembra (DAP)', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0.05, 0.45]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} 
                  formatter={(val: any) => [`${(Number(val) * 100).toFixed(1)}% vol`, '']}
                  labelFormatter={(dap) => `DAP ${dap}`}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <ReferenceLine y={simulation.soilDynamics.fieldCapacity} stroke="#10b981" strokeDasharray="4 4" label={{ value: 'Cap. Campo (FC)', fill: '#10b981', fontSize: 10 }} />
                <ReferenceLine y={simulation.soilDynamics.wiltingPoint} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Pto. Marchitez (WP)', fill: '#ef4444', fontSize: 10 }} />
                <Line type="monotone" dataKey="soilMoistureTop" name="0-30 cm (Topsoil)" stroke="#06b6d4" strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="soilMoistureMid" name="30-60 cm (Subsoil)" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="soilMoistureDeep" name="60-100 cm (Deep Horizon)" stroke="#8b5cf6" strokeWidth={1.8} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Chart 2: Biomass & LAI */}
        {activeChartView === 'biomass_lai' && (
          <div className="h-[320px] w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={simulation.dailyRecords} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="dap" stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: 'DAP', position: 'insideBottom', fill: '#64748b', fontSize: 11 }} />
                <YAxis yAxisId="left" stroke="#10b981" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}t`} />
                <YAxis yAxisId="right" orientation="right" stroke="#06b6d4" tick={{ fontSize: 11 }} domain={[0, 6]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                  labelFormatter={(dap) => `DAP ${dap}`}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Area yAxisId="left" type="monotone" dataKey="biomassKgHa" name="Biomasa Total (kg/ha)" fill="#065f46" stroke="#10b981" strokeWidth={2} />
                <Line yAxisId="right" type="monotone" dataKey="lai" name="Índice Área Foliar (LAI m²/m²)" stroke="#06b6d4" strokeWidth={2.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Chart 3: Water Balance */}
        {activeChartView === 'water_fluxes' && (
          <div className="h-[320px] w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={simulation.dailyRecords} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="dap" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: 'mm / día', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar dataKey="precipitationMm" name="Lluvia (mm)" fill="#38bdf8" />
                <Bar dataKey="irrigationMm" name="Riego Aplicado (mm)" fill="#6366f1" />
                <Line type="monotone" dataKey="transpirationMm" name="Transpiración Cultivo (mm)" stroke="#10b981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="etoMm" name="ETo Referencial (mm)" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Chart 4: Stress CWSI */}
        {activeChartView === 'stress_cwsi' && (
          <div className="h-[320px] w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={simulation.dailyRecords} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="dap" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 1]} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <ReferenceLine y={0.45} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Umbral Sequía Severa (0.45)', fill: '#ef4444', fontSize: 10 }} />
                <Area type="monotone" dataKey="cwsi" name="Índice Estrés Hídrico (CWSI)" fill="#7f1d1d" stroke="#ef4444" strokeWidth={2.5} />
                <Line type="monotone" dataKey="thermalStressFactor" name="Factor Estrés Térmico" stroke="#f59e0b" strokeWidth={1.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};
