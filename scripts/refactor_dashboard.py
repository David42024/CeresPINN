import os
import re

file_path = "src/components/MainDashboard.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the GCM Ensemble block
gcm_start = "{/* GCM Ensemble Uncertainty Analysis */}"
gcm_end = "{/* Interactive Time-Series Charts Section */}"

start_idx = content.find(gcm_start)
end_idx = content.find(gcm_end)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]

# Update the Projected Yield KPI
kpi_yield_start = "{/* KPI 1: Projected Yield */}"
kpi_yield_end = "{/* KPI 2: Water Stress Index */}"

kpi_idx_start = content.find(kpi_yield_start)
kpi_idx_end = content.find(kpi_yield_end)

kpi_yield_old = content[kpi_idx_start:kpi_idx_end]

kpi_yield_new = """{/* KPI 1: Projected Yield */}
        <div id="kpi-projected-yield" className="p-4 rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-lg relative overflow-hidden group hover:border-emerald-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1">
              {t('mainDashboard.kpiProjectedYield')}
              <span className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-[9px] text-slate-500 border border-slate-200 dark:border-slate-700" title="Proviene del modelo de Machine Learning entrenado (CeresYield)">
                {simulation.componentProvenance?.yield === 'trained_model' ? 'ML' : 'SIM'}
              </span>
            </span>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/80 text-emerald-500 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 dark:text-slate-100 font-mono tracking-tight">
              {kpi.projectedYieldKgHa.toLocaleString()}
            </span>
            <span className="text-xs text-slate-600 dark:text-slate-400 font-mono">kg/ha</span>
          </div>
          
          <div className="mt-1 flex items-center gap-1.5 text-[10px]">
            <span className="text-slate-500 dark:text-slate-400">
              IC 90%: {Math.round(simulation.predictionInterval90?.lowerKgHa || kpi.projectedYieldKgHa * 0.9).toLocaleString()} - {Math.round(simulation.predictionInterval90?.upperKgHa || kpi.projectedYieldKgHa * 1.1).toLocaleString()}
            </span>
            {simulation.isExtrapolation && (
              <span className="text-rose-500 font-semibold px-1 py-0.5 bg-rose-50 dark:bg-rose-950/50 rounded flex items-center" title={`Fuera de dominio: ${simulation.extrapolatedFeatures?.join(', ')}`}>
                <AlertTriangle className="w-3 h-3 mr-0.5" /> Extrapolando
              </span>
            )}
          </div>

          <div className="mt-2 flex items-center justify-between text-xs pt-2 border-t border-slate-200/80 dark:border-slate-800/80">
            <span className="text-slate-500 dark:text-slate-500">{t('mainDashboard.kpiPotential')} {(kpi.potentialYieldKgHa / 1000).toFixed(1)} t/ha</span>
            <span className={`font-semibold flex items-center ${
              kpi.yieldLossDueToDroughtPercent > 20 ? 'text-rose-500 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'
            }`}>
              {kpi.yieldLossDueToDroughtPercent > 20 ? <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" /> : <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />}
              {kpi.yieldLossDueToDroughtPercent > 0 ? `-${kpi.yieldLossDueToDroughtPercent}%` : t('mainDashboard.kpiOptimal')}
            </span>
          </div>
        </div>

        """

content = content.replace(kpi_yield_old, kpi_yield_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated MainDashboard.tsx")
