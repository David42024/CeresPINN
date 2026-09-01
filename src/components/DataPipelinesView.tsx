import React, { useState } from 'react';
import { 
  Database, 
  RefreshCw, 
  CloudRain, 
  Satellite, 
  Globe, 
  CheckCircle2, 
  Clock, 
  Radio, 
  ExternalLink,
  Layers,
  Sparkles
} from 'lucide-react';
import { INGESTION_PIPELINES } from '../data/mockData';
import { IngestionPipeline } from '../types';
import { listPipelines, triggerPipelineSync, getPipelineJob } from '../services/api';
import { useEffect, useCallback } from 'react';

export const DataPipelinesView: React.FC = () => {
  const [pipelines, setPipelines] = useState<IngestionPipeline[]>(INGESTION_PIPELINES);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null);
  const [pendingSync, setPendingSync] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<{ [id: string]: number }>({});

  // Merge server status (when reachable) over the local seed, preserving local fields.
  const applyServerStatus = useCallback((serverPipelines: any[]) => {
    setPipelines(prev => prev.map(local => {
      const server = serverPipelines.find((s: any) => s.id === local.id);
      if (!server) return local;
      return {
        ...local,
        status: server.status === 'healthy' ? 'healthy'
              : server.status === 'error' ? 'error'
              : server.status === 'empty' ? 'warning'
              : local.status,
        lastSync: server.lastSync && server.lastSync !== '-' ? server.lastSync : local.lastSync,
        recordsProcessed: server.recordsProcessed !== '-' && server.recordsProcessed
          ? server.recordsProcessed : local.recordsProcessed,
      };
    }));
  }, []);

  // On mount, try to read live pipeline status from the backend.
  useEffect(() => {
    let active = true;
    (async () => {
      const result = await listPipelines();
      if (!active) return;
      if (!result.fallback && Array.isArray(result.pipelines)) {
        setBackendAvailable(true);
        applyServerStatus(result.pipelines);
      } else {
        setBackendAvailable(false);
      }
    })();
    return () => { active = false; };
  }, [applyServerStatus]);

  const handleTriggerSync = async (id: string) => {
    setSyncingId(id);
    setPendingSync(id);
    setJobProgress(prev => ({ ...prev, [id]: 0 }));

    const result = await triggerPipelineSync(id);

    // Real backend path: poll the background job until it settles.
    if (!result.fallback && result.jobId) {
      const jobId = result.jobId;
      let settled = false;
      let attempts = 0;
      while (!settled && attempts < 120) {
        // Delay between polls (progress in real extractions is non-trivial).
        await new Promise(res => setTimeout(res, 400));
        const job = await getPipelineJob(jobId);
        if (job) {
          setJobProgress(prev => ({ ...prev, [id]: Math.max(prev[id] ?? 0, job.percent ?? 0) }));
          if (job.status === 'done' || job.status === 'error') {
            settled = true;
          }
        }
        attempts += 1;
      }
    }

    // After a real (non-fallback) sync completes, refresh the true status.
    if (!result.fallback) {
      const refresh = await listPipelines();
      if (!refresh.fallback && Array.isArray(refresh.pipelines)) {
        applyServerStatus(refresh.pipelines);
      }
    }

    setBackendAvailable(!result.fallback);
    setSyncingId(null);
    setPendingSync(null);
    setJobProgress(prev => ({ ...prev, [id]: 100 }));
  };

  return (
    <div id="data-pipelines-view" className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            Pipelines de Ingesta y Calibración de Datos Públicos
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Orquestación automatizada de descargas satelitales CHIRPS, proyecciones CMIP6 y estadísticas agroclimáticas USDA.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-mono border ${
            backendAvailable === false
              ? 'bg-amber-950/80 border-amber-800/60 text-amber-300'
              : 'bg-emerald-950/80 border-emerald-800/60 text-emerald-300'
          }`}>
            <Radio className={`w-3.5 h-3.5 ${backendAvailable === false ? 'text-amber-400' : 'text-emerald-400 animate-pulse'}`} />
            {backendAvailable === false
              ? 'Backend no disponible · modo fallback local'
              : backendAvailable === null
                ? 'Verificando backend...'
                : 'Backend FastAPI conectado · extracción real'}
          </span>
        </div>
      </div>

      {/* Pipelines Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {pipelines.map((pipe) => {
          const isSyncing = syncingId === pipe.id;
          return (
            <div
              key={pipe.id}
              className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-all"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-slate-900 text-emerald-400 border border-slate-800">
                      {pipe.id === 'pipe-chirps' ? <CloudRain className="w-5 h-5 text-cyan-400" /> :
                       pipe.id === 'pipe-nasa-nex' ? <Satellite className="w-5 h-5 text-amber-400" /> :
                       <Globe className="w-5 h-5 text-emerald-400" />}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-100 leading-tight">{pipe.name}</h3>
                      <span className="text-[11px] text-slate-400 font-mono">{pipe.frequency}</span>
                    </div>
                  </div>

                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 ${
                    pipe.status === 'healthy'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : pipe.status === 'warning'
                        ? 'bg-amber-500/20 text-amber-400'
                        : pipe.status === 'error'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-slate-500/20 text-slate-400'
                  }`}>
                    {pipe.status === 'healthy' ? <><CheckCircle2 className="w-3 h-3" /> Saludable</>
                     : pipe.status === 'warning' ? <><Clock className="w-3 h-3" /> Vacío</>
                     : pipe.status === 'error' ? <><RefreshCw className="w-3 h-3" /> Error</>
                     : <><Clock className="w-3 h-3" /> Sin sync</>}
                  </span>
                </div>

                <p className="text-xs text-slate-300 mt-3 leading-relaxed">{pipe.description}</p>

                {/* Technical stats */}
                <div className="mt-3 space-y-1.5 text-[11px] pt-3 border-t border-slate-800/80 font-mono">
                  <div className="flex justify-between text-slate-400">
                    <span>Fuente:</span>
                    <span className="text-slate-200 truncate max-w-[170px]">{pipe.source}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Resolución:</span>
                    <span className="text-slate-200">{pipe.resolution}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Registros:</span>
                    <span className="text-cyan-300 font-bold">{pipe.recordsProcessed}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Último Sync:</span>
                    <span className="text-slate-300">{pipe.lastSync}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-1.5">
                {isSyncing && (
                  <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-emerald-400 transition-all duration-300"
                      style={{ width: `${jobProgress[pipe.id] ?? 0}%` }}
                    />
                  </div>
                )}
                <button
                  onClick={() => handleTriggerSync(pipe.id)}
                  disabled={isSyncing}
                  className="w-full py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-semibold text-xs flex items-center justify-center gap-1.5 border border-slate-700 transition-all disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${isSyncing ? 'animate-spin' : ''}`} />
                  {isSyncing
                    ? `${jobProgress[pipe.id] ?? 0}% · Sincronizando NetCDF...`
                    : backendAvailable === false
                      ? 'Sincronizar (fallback local)'
                      : 'Forzar Sincronización Inmediata'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
