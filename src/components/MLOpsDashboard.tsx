import React, { useState } from 'react';
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
  CartesianGrid 
} from 'recharts';
import { MODEL_REGISTRY_DATA } from '../data/mockData';
import { ModelRegistryEntry } from '../types';

export const MLOpsDashboard: React.FC = () => {
  const [models, setModels] = useState<ModelRegistryEntry[]>(MODEL_REGISTRY_DATA);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);
  const [retrainEpoch, setRetrainEpoch] = useState<number>(0);
  const [lambdaPde, setLambdaPde] = useState<number>(0.45);
  const [learningRate, setLearningRate] = useState<number>(0.001);
  const [batchSize, setBatchSize] = useState<number>(64);

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
    <div id="mlops-pinn-dashboard" className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-emerald-400" />
            Administración del Modelo PINN & MLOps Registry
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Supervisión de pérdidas PDE (Richards flow residual), re-entrenamiento continuo y versionado de pesos neuronales.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-xl bg-violet-950/80 border border-violet-800/60 text-violet-300 text-xs font-mono flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-300" />
            Motor de Inferencia: PyTorch / LibTorch C++ JIT
          </span>
        </div>
      </div>

      {/* Grid: Loss Curves Chart + Retraining Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: PINN Decomposition Loss Chart */}
        <div className="lg:col-span-7 bg-slate-950 rounded-xl border border-slate-800 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              Descomposición de Funciones de Pérdida PINN (Training Convergence)
            </h3>
            <span className="text-[11px] font-mono text-emerald-400">R² = 0.942 | RMSE = 385 kg/ha</span>
          </div>

          <div className="h-[260px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lossHistoryData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 11 }} label={{ value: 'Épocas', position: 'insideBottom', fill: '#64748b', fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                <Line type="monotone" dataKey="totalLoss" name="Loss Total L_total" stroke="#f43f5e" strokeWidth={2.5} />
                <Line type="monotone" dataKey="pdeLoss" name="Residual PDE Richards (λ·L_pde)" stroke="#06b6d4" strokeWidth={2} />
                <Line type="monotone" dataKey="dataLoss" name="Datos Empíricos NASS (L_data)" stroke="#10b981" strokeWidth={1.8} />
                <Line type="monotone" dataKey="boundaryLoss" name="Cond. Contorno (L_bc)" stroke="#a855f7" strokeWidth={1.5} strokeDasharray="3 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="text-[11px] text-slate-400 p-2.5 rounded-lg bg-slate-900/90 border border-slate-800/80 leading-relaxed font-mono">
            {`L_total = L_data(θ, y) + λ_PDE · ‖∂θ/∂t - ∂/∂z(K(h)(∂h/∂z + 1)) + S(z,t)‖² + λ_BC · L_BC`}
          </div>
        </div>

        {/* Right: Retraining Form */}
        <div className="lg:col-span-5 bg-slate-950 rounded-xl border border-slate-800 p-4 flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-1.5 mb-3">
              <Sliders className="w-4 h-4 text-emerald-400" />
              Re-entrenar Red Neuronal PINN
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Peso Regularizador Richards (λ_PDE)</span>
                  <span className="font-mono text-cyan-300 font-bold">{lambdaPde}</span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  value={lambdaPde}
                  onChange={(e) => setLambdaPde(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Tasa de Aprendizaje (Learning Rate $\eta$)</span>
                  <span className="font-mono text-emerald-300 font-bold">{learningRate}</span>
                </div>
                <select
                  value={learningRate}
                  onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value={0.005}>0.005 (Rápido)</option>
                  <option value={0.001}>0.001 (Estándar AdamW)</option>
                  <option value={0.0001}>0.0001 (Fine-Tuning Fino)</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Tamaño de Batch</span>
                  <span className="font-mono text-violet-300 font-bold">{batchSize}</span>
                </div>
                <select
                  value={batchSize}
                  onChange={(e) => setBatchSize(parseInt(e.target.value, 10))}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                >
                  <option value={32}>32</option>
                  <option value={64}>64 (Óptimo GPU)</option>
                  <option value={128}>128</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            {isRetraining && (
              <div className="space-y-1.5 mb-3">
                <div className="flex justify-between text-[11px] font-mono text-emerald-400">
                  <span>Optimizando Tensores PyTorch...</span>
                  <span>{retrainEpoch}%</span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
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
              {isRetraining ? 'Entrenando Épocas...' : 'Iniciar Re-entrenamiento PINN'}
            </button>
          </div>
        </div>
      </div>

      {/* Model Registry List */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Registro de Versiones (Model Registry)
        </h3>

        <div className="space-y-2">
          {models.map((model) => (
            <div
              key={model.version}
              className={`p-3.5 rounded-xl border flex flex-wrap items-center justify-between gap-3 transition-all ${
                model.active 
                  ? 'bg-emerald-950/40 border-emerald-500 shadow-md shadow-emerald-950/40' 
                  : 'bg-slate-950/60 border-slate-800'
              }`}
            >
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-slate-100">{model.name}</h4>
                  <span className="px-2 py-0.5 rounded-md bg-slate-800 font-mono text-[10px] text-slate-300">
                    {model.version}
                  </span>
                  {model.active && (
                    <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      Activo en Producción
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{model.description}</p>
              </div>

              <div className="flex items-center gap-4 text-xs font-mono">
                <div className="text-right">
                  <span className="text-slate-500 block text-[10px]">R² Test</span>
                  <span className="text-emerald-400 font-bold">{model.testR2}</span>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block text-[10px]">RMSE</span>
                  <span className="text-cyan-300 font-bold">{model.testRmseKgHa} kg/ha</span>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block text-[10px]">Épocas</span>
                  <span className="text-slate-300">{model.epochs.toLocaleString()}</span>
                </div>

                {!model.active && (
                  <button
                    onClick={() => handleSetActiveModel(model.version)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition-all"
                  >
                    Activar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
