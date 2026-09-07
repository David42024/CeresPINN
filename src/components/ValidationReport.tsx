import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  TrendingUp, 
  BarChart3, 
  Activity, 
  CheckCircle, 
  AlertTriangle,
  RefreshCw,
  Info
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  CartesianGrid,
  BarChart,
  Bar
} from 'recharts';
import { fetchValidationReport, fetchHindcastData } from '../services/api';

export const ValidationReport: React.FC = () => {
  const [validationData, setValidationData] = useState<any>(null);
  const [hindcastData, setHindcastData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isFallback, setIsFallback] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [validation, hindcast] = await Promise.all([
          fetchValidationReport(),
          fetchHindcastData()
        ]);
        
        if (!validation.fallback) {
          setValidationData(validation.report);
          setIsFallback(false);
        } else {
          setValidationData(validation.report);
          setIsFallback(true);
        }
        
        if (!hindcast.fallback) {
          setHindcastData(hindcast.hindcast);
        } else {
          setHindcastData(hindcast.hindcast);
        }
      } catch (error) {
        console.error('Failed to load validation data', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    const [validation, hindcast] = await Promise.all([
      fetchValidationReport(),
      fetchHindcastData()
    ]);
    
    if (!validation.fallback) {
      setValidationData(validation.report);
      setIsFallback(false);
    } else {
      setValidationData(validation.report);
      setIsFallback(true);
    }
    
    if (!hindcast.fallback) {
      setHindcastData(hindcast.hindcast);
    } else {
      setHindcastData(hindcast.hindcast);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl">
        <div className="flex items-center justify-center py-20 text-slate-500 dark:text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-3" />
          Cargando reporte de validación estadística...
        </div>
      </div>
    );
  }

  const hindcastChartData = hindcastData?.years?.map((year: number, idx: number) => ({
    year,
    observed: hindcastData.observed_yield[idx],
    predicted: hindcastData.predicted_yield[idx],
    residual: hindcastData.residuals[idx]
  })) || [];

  const sobolData = validationData?.sobol_sensitivity?.first_order ? 
    Object.entries(validationData.sobol_sensitivity.first_order).map(([key, value]) => ({
      parameter: key.charAt(0).toUpperCase() + key.slice(1),
      firstOrder: value as number,
      totalOrder: (validationData.sobol_sensitivity.total_order as any)[key] as number
    })) : [];

  return (
    <div id="validation-report" className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Validación Estadística del Modelo PINN
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Hindcast histórico, pruebas KS, t-test pareado, análisis de sensibilidad Sobol y bootstrap de incertidumbre.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isFallback && (
            <span className="px-3 py-1 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-mono flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              Modo Fallback (Datos Locales)
            </span>
          )}
          <button
            onClick={handleRefresh}
            className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Actualizar
          </button>
        </div>
      </div>

      {/* Hindcast Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-500 text-[11px] block">RMSE (kg/ha)</span>
          <strong className="text-emerald-400 font-mono text-lg">{validationData?.hindcast_metrics?.rmse_kg_ha || 0}</strong>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-500 text-[11px] block">MAE (kg/ha)</span>
          <strong className="text-cyan-400 font-mono text-lg">{validationData?.hindcast_metrics?.mae_kg_ha || 0}</strong>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-500 text-[11px] block">R² Score</span>
          <strong className="text-violet-400 font-mono text-lg">{validationData?.hindcast_metrics?.r2_score?.toFixed(3) || 0}</strong>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-500 text-[11px] block">NRMSE (%)</span>
          <strong className="text-amber-400 font-mono text-lg">{validationData?.hindcast_metrics?.nrmse_percent?.toFixed(1) || 0}%</strong>
        </div>
      </div>

      {/* Hindcast Chart */}
      <div className="bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          Hindcast Histórico: Rendimiento Observado vs Predicho (2015-2024)
        </h3>
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={hindcastChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="year" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
              <Line type="monotone" dataKey="observed" name="Observado" stroke="#10b981" strokeWidth={2.5} />
              <Line type="monotone" dataKey="predicted" name="Predicho PINN" stroke="#06b6d4" strokeWidth={2.5} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Statistical Tests Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* KS Test */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-cyan-400" />
            Prueba Kolmogorov-Smirnov
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-slate-400">Estadístico KS</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{validationData?.ks_test?.statistic?.toFixed(3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-slate-400">Valor p</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{validationData?.ks_test?.p_value?.toFixed(3)}</span>
            </div>
            <div className="flex items-center gap-2 pt-2">
              {validationData?.ks_test?.null_rejected ? (
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              ) : (
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              )}
              <span className={validationData?.ks_test?.null_rejected ? "text-rose-400" : "text-emerald-400"}>
                {validationData?.ks_test?.null_rejected ? "Hipótesis nula rechazada" : "Distribuciones similares"}
              </span>
            </div>
          </div>
        </div>

        {/* Paired t-test */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
            <BarChart3 className="w-4 h-4 text-violet-400" />
            T-Test Pareado (SSP5-8.5 vs Histórico)
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-slate-400">Estadístico t</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{validationData?.paired_t_test?.t_statistic?.toFixed(3)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-slate-400">Valor p</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{validationData?.paired_t_test?.p_value?.toFixed(3)}</span>
            </div>
            <div className="flex items-center gap-2 pt-2">
              {validationData?.paired_t_test?.significant ? (
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              ) : (
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              )}
              <span className={validationData?.paired_t_test?.significant ? "text-rose-400" : "text-emerald-400"}>
                {validationData?.paired_t_test?.significant ? "Diferencia significativa" : "Sin diferencia significativa"}
              </span>
            </div>
          </div>
        </div>

        {/* Bootstrap CI */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
            <Info className="w-4 h-4 text-amber-400" />
            Intervalo de Confianza Bootstrap (95%)
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-slate-400">Límite Inferior</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{validationData?.bootstrap_ci?.yield_95_ci_lower?.toLocaleString()} kg/ha</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-slate-400">Límite Superior</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{validationData?.bootstrap_ci?.yield_95_ci_upper?.toLocaleString()} kg/ha</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-slate-400">Muestras Bootstrap</span>
              <span className="font-mono text-slate-800 dark:text-slate-200">{validationData?.bootstrap_ci?.n_bootstrap?.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sobol Sensitivity Analysis */}
      <div className="bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
          <BarChart3 className="w-4 h-4 text-rose-400" />
          Análisis de Sensibilidad Sobol (Índices de Sobol)
        </h3>
        <div className="h-[240px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sobolData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="parameter" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
              <Bar dataKey="firstOrder" name="Primer Orden (S₁)" fill="#10b981" />
              <Bar dataKey="totalOrder" name="Orden Total (Sₜ)" fill="#06b6d4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Ensemble Uncertainty */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-500 text-[11px] block">Rendimiento Promedio Ensemble</span>
          <strong className="text-emerald-400 font-mono text-lg">{validationData?.ensemble_uncertainty?.mean_yield?.toLocaleString()} kg/ha</strong>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-500 text-[11px] block">Desviación Estándar</span>
          <strong className="text-cyan-400 font-mono text-lg">{validationData?.ensemble_uncertainty?.std_yield?.toLocaleString()} kg/ha</strong>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-500 text-[11px] block">Tamaño del Ensemble</span>
          <strong className="text-violet-400 font-mono text-lg">{validationData?.ensemble_uncertainty?.ensemble_size} modelos</strong>
        </div>
      </div>
    </div>
  );
};
