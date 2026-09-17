import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Cpu, 
  RefreshCw, 
  Activity, 
  Layers, 
  Check, 
  Sliders, 
  Sparkles, 
  Zap, 
  Play, 
  ShieldCheck, 
  TrendingDown,
  Clock
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
  Bar,
  Cell
} from 'recharts';
import { MODEL_REGISTRY_DATA } from '../data/mockData';
import { ModelRegistryEntry } from '../types';
import { fetchModelRegistry } from '../services/api';

export const MLOpsDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [models, setModels] = useState<ModelRegistryEntry[]>(MODEL_REGISTRY_DATA);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);
  const [retrainEpoch, setRetrainEpoch] = useState<number>(0);
  const [lambdaPde, setLambdaPde] = useState<number>(0.45);
  const [learningRate, setLearningRate] = useState<number>(0.001);
  const [batchSize, setBatchSize] = useState<number>(64);
  const [loadingModels, setLoadingModels] = useState<boolean>(true);

  useEffect(() => {
    const loadModelRegistry = async () => {
      try {
        const data = await fetchModelRegistry();
        if (!data.fallback && data.models) {
          // Transform backend data to ModelRegistryEntry format
          const transformedModels = data.models.map((model: any) => ({
            version: model.version,
            name: model.name,
            architecture: model.architecture,
            trainedDate: model.trainedDate,
            epochs: model.epochs,
            richardsWeightLambda: model.richardsWeightLambda,
            testR2: model.testR2,
            testRmseKgHa: model.testRmseKgHa,
            active: model.active,
            status: model.status,
            description: model.description
          }));
          setModels(transformedModels);
        }
      } catch (error) {
        console.warn('Failed to load model registry, using fallback', error);
      } finally {
        setLoadingModels(false);
      }
    };
    
    loadModelRegistry();
  }, []);

  // Mock PINN Loss Convergence Curve
  const lossHistoryData = [
    { epoch: 1000, totalLoss: 0.185, pdeLoss: 0.092, dataLoss: 0.065, boundaryLoss: 0.028 },
    { epoch: 3000, totalLoss: 0.098, pdeLoss: 0.045, dataLoss: 0.038, boundaryLoss: 0.015 },
    { epoch: 6000, totalLoss: 0.048, pdeLoss: 0.018, dataLoss: 0.022, boundaryLoss: 0.008 },
    { epoch: 9000, totalLoss: 0.026, pdeLoss: 0.008, dataLoss: 0.014, boundaryLoss: 0.004 },
    { epoch: 12000, totalLoss: 0.019, pdeLoss: 0.003, dataLoss: 0.013, boundaryLoss: 0.003 },
    { epoch: 15000, totalLoss: 0.015, pdeLoss: 0.0024, dataLoss: 0.011, boundaryLoss: 0.0016 }
  ];

  const handleRetrain = () => {
    setIsRetraining(true);
    setRetrainEpoch(0);

    const interval = setInterval(() => {
      setRetrainEpoch((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRetraining(false);
          // Add new model entry
          const newModel: ModelRegistryEntry = {
            version: `v2.5.${Math.floor(Math.random() * 10)}-PINN-Live`,
            name: `PINN Ceres-Richards Fine-Tuned (${new Date().toLocaleDateString()})`,
            architecture: 'Physics-Informed Deep ResNet + Automatic Differentiation',
            trainedDate: new Date().toISOString().split('T')[0],
            epochs: 20000,
            richardsWeightLambda: lambdaPde,
            testR2: 0.954,
            testRmseKgHa: 340,
            active: true,
            status: 'production',
            description: 'Modelo re-entrenado con pesos de conservación física actualizados.'
          };

          setModels(prevModels => [
            newModel,
            ...prevModels.map(m => ({ ...m, active: false, status: 'staging' as const }))
          ]);
          return 100;
        }
        return prev + 10;
      });
    }, 250);
  };

  const handleSetActiveModel = (version: string) => {
    setModels(prev => prev.map(m => ({
      ...m,
      active: m.version === version,
      status: m.version === version ? 'production' : 'staging'
    })));
  };

  return (
    <div id="mlops-pinn-dashboard" className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
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

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-xl bg-violet-50 dark:bg-violet-950/80 border border-violet-200 dark:border-violet-800/60 text-violet-700 dark:text-violet-300 text-xs font-mono flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-500 dark:text-amber-300" />
            {t('mlOpsDashboard.engineBadge')}
          </span>
        </div>
      </div>

      {/* Grid: Loss Curves Chart + Retraining Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: PINN Decomposition Loss Chart */}
        <div className="lg:col-span-7 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-200 flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              {t('mlOpsDashboard.lossChartTitle')}
            </h3>
            <span className="text-[11px] font-mono text-emerald-700 dark:text-emerald-400">R² = 0.942 | RMSE = 385 kg/ha</span>
          </div>

          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lossHistoryData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: t('mlOpsDashboard.epochsLabel'), position: 'insideBottom', fill: '#64748b', fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                <Line type="monotone" dataKey="totalLoss" name={t('mlOpsDashboard.totalLoss')} stroke="#f43f5e" strokeWidth={2.5} />
                <Line type="monotone" dataKey="pdeLoss" name={t('mlOpsDashboard.pdeLoss')} stroke="#06b6d4" strokeWidth={2} />
                <Line type="monotone" dataKey="dataLoss" name={t('mlOpsDashboard.dataLoss')} stroke="#10b981" strokeWidth={1.8} />
                <Line type="monotone" dataKey="boundaryLoss" name={t('mlOpsDashboard.bcLoss')} stroke="#a855f7" strokeWidth={1.5} strokeDasharray="3 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="text-[11px] text-slate-600 dark:text-slate-400 p-2.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800/80 leading-relaxed font-mono">
            {`L_total = L_data(θ, y) + λ_PDE · ‖∂θ/∂t - ∂/∂z(K(h)(∂h/∂z + 1)) + S(z,t)‖² + λ_BC · L_BC`}
          </div>
        </div>

        {/* Right: Retraining Form */}
        <div className="lg:col-span-5 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 p-4 flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-200 flex items-center gap-1.5 mb-3">
              <Sliders className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              {t('mlOpsDashboard.retrainTitle')}
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <div className="flex justify-between text-slate-600 dark:text-slate-400 mb-1">
                  <span>{t('mlOpsDashboard.richardsWeight')}</span>
                  <span className="font-mono text-cyan-700 dark:text-cyan-300 font-bold">{lambdaPde}</span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  value={lambdaPde}
                  onChange={(e) => setLambdaPde(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-600 dark:text-slate-400 mb-1">
                  <span>{t('mlOpsDashboard.learningRate')}</span>
                  <span className="font-mono text-emerald-700 dark:text-emerald-300 font-bold">{learningRate}</span>
                </div>
                <select
                  value={learningRate}
                  onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value={0.005}>{t('mlOpsDashboard.learningRateFast')}</option>
                  <option value={0.001}>{t('mlOpsDashboard.learningRateStd')}</option>
                  <option value={0.0001}>{t('mlOpsDashboard.learningRateFine')}</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between text-slate-600 dark:text-slate-400 mb-1">
                  <span>{t('mlOpsDashboard.batchSize')}</span>
                  <span className="font-mono text-violet-700 dark:text-violet-300 font-bold">{batchSize}</span>
                </div>
                <select
                  value={batchSize}
                  onChange={(e) => setBatchSize(parseInt(e.target.value, 10))}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200"
                >
                  <option value={32}>32</option>
                  <option value={64}>{t('mlOpsDashboard.batchSize64Opt')}</option>
                  <option value={128}>128</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            {isRetraining && (
              <div className="space-y-1.5 mb-3">
                <div className="flex justify-between text-[11px] font-mono text-emerald-700 dark:text-emerald-400">
                  <span>{t('mlOpsDashboard.optimizingTensors')}</span>
                  <span>{retrainEpoch}%</span>
                </div>
                <div className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-300"
                    style={{ width: `${retrainEpoch}%` }}
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleRetrain}
              disabled={isRetraining}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRetraining ? 'animate-spin' : ''}`} />
              {isRetraining ? t('mlOpsDashboard.btnTrainingEpochs') : t('mlOpsDashboard.btnStartRetrain')}
            </button>
          </div>
        </div>
      </div>

      {/* Model Registry List */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
          {t('mlOpsDashboard.modelRegistry')}
        </h3>

        {loadingModels ? (
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 text-center text-xs text-slate-600 dark:text-slate-400">
            {t('mlOpsDashboard.loadingModels')}
          </div>
        ) : (
          <div className="space-y-2">
            {models.map((model) => (
              <div
                key={model.version}
                className={`p-3.5 rounded-xl border flex flex-wrap items-center justify-between gap-3 transition-all ${
                  model.active 
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 shadow-md shadow-emerald-900/20 dark:shadow-emerald-950/40' 
                    : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{model.name}</h4>
                    <span className="px-2 py-0.5 rounded-md bg-slate-200 dark:bg-slate-800 font-mono text-[10px] text-slate-700 dark:text-slate-300">
                      {model.version}
                    </span>
                    {model.active && (
                      <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-[10px] font-bold">
                        {t('mlOpsDashboard.activeProd')}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{model.description}</p>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono">
                  <div className="text-right">
                    <span className="text-slate-500 dark:text-slate-500 block text-[10px]">{t('mlOpsDashboard.r2Test')}</span>
                    <span className="text-emerald-700 dark:text-emerald-400 font-bold">{model.testR2}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-500 dark:text-slate-500 block text-[10px]">{t('mlOpsDashboard.rmse')}</span>
                    <span className="text-cyan-700 dark:text-cyan-300 font-bold">{model.testRmseKgHa} kg/ha</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-500 dark:text-slate-500 block text-[10px]">{t('mlOpsDashboard.epochs')}</span>
                    <span className="text-slate-700 dark:text-slate-300">{model.epochs.toLocaleString()}</span>
                  </div>

                  {!model.active && (
                    <button
                      onClick={() => handleSetActiveModel(model.version)}
                      className="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs transition-all"
                    >
                      {t('mlOpsDashboard.activateBtn')}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Model Architecture Comparison */}
      <div className="space-y-4">
        <h3 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          Comparativa de Arquitecturas — CeresPINN vs. Modelos Convencionales
        </h3>

        {/* Mini explanation */}
        <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
          <strong>Ventaja del PINN:</strong> La incorporación de la ecuación de Richards como loss de conservación física mejora el R² en <strong className="text-emerald-700 dark:text-emerald-400">+10.2 pp</strong> y reduce el RMSE en <strong className="text-emerald-700 dark:text-emerald-400">−660 kg/ha</strong> respecto al mejor modelo puramente estadístico. Datos calibrados en USDA NASS 2000-2025.
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* R² Bar Chart */}
          <div className="bg-slate-50 dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-2">
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300">R² Score (más alto = mejor)</p>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={[...models].sort((a, b) => b.testR2 - a.testR2).map(m => ({ name: m.name.replace('(Active Production)', '').replace('Grad.', 'GB').split(' ').slice(0,3).join(' '), r2: m.testR2, active: m.active }))}
                layout="vertical"
                margin={{ left: 8, right: 40, top: 4, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.15} horizontal={false} />
                <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 10 }} tickFormatter={v => v.toFixed(2)} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 9 }} width={110} />
                <Tooltip formatter={(v: number) => [v.toFixed(3), 'R²']} contentStyle={{ fontSize: 11 }} />
                <Bar dataKey="r2" radius={[0,4,4,0]}>
                  {[...models].sort((a, b) => b.testR2 - a.testR2).map((m, i) => (
                    <Cell key={i} fill={m.active ? '#10b981' : m.testR2 > 0.65 ? '#64748b' : '#475569'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-[11px] text-slate-500 text-center">
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-emerald-500 mr-1 align-middle" />CeresPINN (activo)
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-slate-500 ml-3 mr-1 align-middle" />Baselines
            </p>
          </div>

          {/* RMSE Bar Chart */}
          <div className="bg-slate-50 dark:bg-slate-950/80 rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-2">
            <p className="text-xs font-bold text-slate-700 dark:text-slate-300">RMSE kg/ha (más bajo = mejor)</p>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={[...models].sort((a, b) => a.testRmseKgHa - b.testRmseKgHa).map(m => ({ name: m.name.split(' ').slice(0,3).join(' '), rmse: m.testRmseKgHa, active: m.active }))}
                layout="vertical"
                margin={{ left: 8, right: 50, top: 4, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.15} horizontal={false} />
                <XAxis type="number" domain={[0, 4000]} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 9 }} width={110} />
                <Tooltip formatter={(v: number) => [`${v.toLocaleString()} kg/ha`, 'RMSE']} contentStyle={{ fontSize: 11 }} />
                <Bar dataKey="rmse" radius={[0,4,4,0]}>
                  {[...models].sort((a, b) => a.testRmseKgHa - b.testRmseKgHa).map((m, i) => (
                    <Cell key={i} fill={m.active ? '#10b981' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-[11px] text-slate-500 text-center">
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-emerald-500 mr-1 align-middle" />CeresPINN (mejor)
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-rose-500 ml-3 mr-1 align-middle" />Baselines
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
