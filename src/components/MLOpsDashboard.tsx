import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, CalendarDays, Cpu, Database, Layers, ShieldCheck } from 'lucide-react';
import { ModelRegistryEntry } from '../types';
import { fetchModelRegistry } from '../services/api';

/**
 * Read-only view of the checkpoint metadata returned by FastAPI.
 *
 * The dashboard deliberately does not synthesize training curves or expose
 * editable controls: the browser has neither the training history nor a secure
 * training runtime. Every number rendered below comes from the deployed
 * checkpoint metadata.
 */
export const MLOpsDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [models, setModels] = useState<ModelRegistryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const loadModel = async () => {
      try {
        const response = await fetchModelRegistry();
        if (!mounted) return;
        if (response.fallback || !response.models?.length) {
          setModels([]);
          setError(t('mlOpsDashboard.unavailable'));
          return;
        }
        setModels(response.models);
        setError(null);
      } catch (requestError) {
        console.warn('Failed to load verified checkpoint metadata', requestError);
        if (mounted) {
          setModels([]);
          setError(t('mlOpsDashboard.unavailable'));
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadModel();
    return () => { mounted = false; };
  }, [t]);

  const activeModel = models.find(model => model.active) ?? models[0];

  return (
    <div id="mlops-pinn-dashboard" className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            {t('mlOpsDashboard.title')}
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            {t('mlOpsDashboard.subtitle')}
          </p>
        </div>
        <span className="px-3 py-1 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-xs font-mono flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5" />
          {t('mlOpsDashboard.verifiedOnly')}
        </span>
      </div>

      {loading ? (
        <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-center text-sm text-slate-600 dark:text-slate-400">
          {t('mlOpsDashboard.loadingModels')}
        </div>
      ) : error || !activeModel ? (
        <div className="p-5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-center text-sm text-rose-700 dark:text-rose-300">
          {error ?? t('mlOpsDashboard.unavailable')}
        </div>
      ) : (
        <>
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{activeModel.name}</h3>
              <span className="px-2 py-0.5 rounded-md bg-slate-200 dark:bg-slate-800 font-mono text-[10px] text-slate-700 dark:text-slate-300">
                {activeModel.version}
              </span>
              <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-[10px] font-bold">
                {t('mlOpsDashboard.activeProd')}
              </span>
            </div>
            <p className="text-xs text-slate-700 dark:text-slate-300">{activeModel.description}</p>
            <p className="text-[11px] text-slate-600 dark:text-slate-400">
              {t('mlOpsDashboard.noSyntheticCurves')}
            </p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <MetricCard icon={<Activity className="w-4 h-4" />} label={t('mlOpsDashboard.r2Test')} value={activeModel.testR2.toFixed(4)} />
            <MetricCard icon={<Activity className="w-4 h-4" />} label={t('mlOpsDashboard.rmse')} value={`${activeModel.testRmseKgHa.toLocaleString()} kg/ha`} />
            <MetricCard icon={<Layers className="w-4 h-4" />} label={t('mlOpsDashboard.epochs')} value={activeModel.epochs.toLocaleString()} />
            <MetricCard icon={<ShieldCheck className="w-4 h-4" />} label={t('mlOpsDashboard.monotonicityWeight')} value={activeModel.monotonicityWeight.toString()} />
            <MetricCard icon={<CalendarDays className="w-4 h-4" />} label={t('mlOpsDashboard.trainedAt')} value={activeModel.trainedDate || '—'} />
          </div>

          <div className="flex items-start gap-2 p-3 rounded-xl bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800/50 text-xs text-slate-700 dark:text-slate-300">
            <Database className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
            <span><strong>{t('mlOpsDashboard.architecture')}:</strong> {activeModel.architecture}</span>
          </div>
        </>
      )}
    </div>
  );
};

const MetricCard: React.FC<{ icon: React.ReactNode; label: string; value: string }> = ({ icon, label, value }) => (
  <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
    <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 text-[10px] uppercase tracking-wide">
      {icon}
      <span>{label}</span>
    </div>
    <div className="mt-1 text-sm font-bold font-mono text-slate-900 dark:text-slate-100">{value}</div>
  </div>
);
