import React, { useState, useEffect } from 'react';
import { 
  Sprout, 
  Activity, 
  Layers, 
  MapPin, 
  Sliders, 
  GitCompare, 
  FileText, 
  Cpu, 
  Database, 
  Users, 
  Play, 
  Calendar, 
  Droplets, 
  Sparkles, 
  ShieldAlert,
  ChevronDown,
  Info,
  HelpCircle,
  Clock,
  Zap,
  Globe
} from 'lucide-react';
import { 
  Field, 
  SimulationConfig, 
  SimulationResult, 
  User 
} from './types';
import { 
  DEFAULT_FIELDS, 
  DEFAULT_SIMULATION_CONFIG, 
  DEMO_USERS 
} from './data/mockData';
import { simulateScenario } from './services/api';
import { runPINNSimulation } from './services/pinnEngine';
import { ThreeFieldViewer } from './components/ThreeFieldViewer';
import { MainDashboard } from './components/MainDashboard';
import { SimulationConfigPanel } from './components/SimulationConfig';
import { WhatIfStudio } from './components/WhatIfStudio';
import { FieldMapManager } from './components/FieldMapManager';
import { ReportsModule } from './components/ReportsModule';
import { MLOpsDashboard } from './components/MLOpsDashboard';
import { DataPipelinesView } from './components/DataPipelinesView';
import { UserManagement } from './components/UserManagement';

type ActiveTab = 
  | 'twin3d' 
  | 'dashboard' 
  | 'config' 
  | 'whatif' 
  | 'map' 
  | 'reports' 
  | 'mlops' 
  | 'pipelines' 
  | 'users';

export const App: React.FC = () => {
  const [fields, setFields] = useState<Field[]>(DEFAULT_FIELDS);
  const [selectedField, setSelectedField] = useState<Field>(DEFAULT_FIELDS[0]);
  const [simulationConfig, setSimulationConfig] = useState<SimulationConfig>(DEFAULT_SIMULATION_CONFIG);
  const [activeTab, setActiveTab] = useState<ActiveTab>('twin3d');
  const [currentUser, setCurrentUser] = useState<User>(DEMO_USERS[0]);
  const [currentDayIndex, setCurrentDayIndex] = useState<number>(65); // Mid-season by default
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Computed simulation result based on field and configuration
  const [simulationResult, setSimulationResult] = useState<SimulationResult>(() => 
    runPINNSimulation(DEFAULT_FIELDS[0], DEFAULT_SIMULATION_CONFIG)
  );

  // Re-run simulation when field or config changes or user triggers run
  const executeSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await simulateScenario(selectedField, simulationConfig);
      setSimulationResult(res);
    } catch (error) {
      console.error('Simulation request failed', error);
      setSimulationResult(runPINNSimulation(selectedField, simulationConfig));
    } finally {
      setIsSimulating(false);
    }
  };

  const handleSelectField = async (field: Field) => {
    setSelectedField(field);
    try {
      const res = await simulateScenario(field, simulationConfig);
      setSimulationResult(res);
    } catch (error) {
      console.error('Simulation request failed for field switch', error);
      setSimulationResult(runPINNSimulation(field, simulationConfig));
    }
  };

  const handleAddField = (newField: Field) => {
    setFields(prev => [...prev, newField]);
  };

  const handleDeleteField = (fieldId: string) => {
    if (fields.length <= 1) return;
    const filtered = fields.filter(f => f.id !== fieldId);
    setFields(filtered);
    if (selectedField.id === fieldId) {
      handleSelectField(filtered[0]);
    }
  };

  const currentDayRecord = simulationResult.dailyRecords[currentDayIndex] || simulationResult.dailyRecords[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navbar */}
      <header id="main-header" className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Scientific Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 via-emerald-500 to-teal-400 p-0.5 shadow-lg shadow-emerald-500/20 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
                <Sprout className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-black tracking-tight text-slate-100 flex items-center gap-1.5">
                  CeresPINN
                  <span className="text-[11px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                    v2.5
                  </span>
                </h1>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                Gemelo Digital Adaptativo al Clima | Maíz Resiliente a Sequías
              </p>
            </div>
          </div>

          {/* Quick Field Selector dropdown & Active Scenario Tag */}
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="relative">
              <select
                id="select-active-field"
                value={selectedField.id}
                onChange={(e) => {
                  const f = fields.find(item => item.id === e.target.value);
                  if (f) handleSelectField(f);
                }}
                className="bg-slate-900 border border-slate-700 text-slate-200 text-xs font-semibold rounded-xl px-3 py-2 pr-8 focus:outline-none focus:border-emerald-500 cursor-pointer appearance-none"
              >
                {fields.map(f => (
                  <option key={f.id} value={f.id}>
                    📍 {f.name} ({f.areaHectares} ha)
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Run button shortcut */}
            <button
              id="btn-quick-run-sim"
              onClick={executeSimulation}
              disabled={isSimulating}
              className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-600/30 transition-all disabled:opacity-50"
              title="Recalcular gemelo digital con las condiciones actuales"
            >
              <Zap className={`w-3.5 h-3.5 text-amber-300 ${isSimulating ? 'animate-spin' : ''}`} />
              <span className="hidden md:inline">{isSimulating ? 'Simulando...' : 'Ejecutar PINN'}</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center gap-1 overflow-x-auto py-1 border-t border-slate-900 text-xs">
          <button
            id="tab-btn-twin3d"
            onClick={() => setActiveTab('twin3d')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'twin3d' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Gemelo 3D & Fenología
          </button>

          <button
            id="tab-btn-dashboard"
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'dashboard' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Dashboard & KPIs
          </button>

          <button
            id="tab-btn-config"
            onClick={() => setActiveTab('config')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'config' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Configuración & Clima
          </button>

          <button
            id="tab-btn-whatif"
            onClick={() => setActiveTab('whatif')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'whatif' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            Estudio What-If
          </button>

          <button
            id="tab-btn-map"
            onClick={() => setActiveTab('map')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'map' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <MapPin className="w-3.5 h-3.5" />
            Gestión GIS de Campos
          </button>

          <button
            id="tab-btn-reports"
            onClick={() => setActiveTab('reports')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'reports' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Reportes & PDF
          </button>

          <button
            id="tab-btn-mlops"
            onClick={() => setActiveTab('mlops')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'mlops' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            MLOps & Modelo PINN
          </button>

          <button
            id="tab-btn-pipelines"
            onClick={() => setActiveTab('pipelines')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'pipelines' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            Pipelines de Ingesta
          </button>

          <button
            id="tab-btn-users"
            onClick={() => setActiveTab('users')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'users' ? 'bg-slate-800 text-emerald-400 border border-slate-700' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            Usuarios & Roles
          </button>
        </div>
      </header>

      {/* Main App Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Status Sub-Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-slate-900/60 border border-slate-800/80 text-xs">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-slate-400">
              Campo: <strong className="text-slate-200">{selectedField.name}</strong> ({selectedField.locationName})
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">
              Escenario: <strong className="text-emerald-400 font-mono">CMIP6 {simulationConfig.scenario} ({simulationConfig.targetYear})</strong>
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">
              Suelo: <strong className="text-cyan-400">{selectedField.soilProfile.label}</strong>
            </span>
          </div>

          <div className="flex items-center gap-3 text-slate-400 font-mono">
            <span>Rendimiento Estimado: <strong className="text-emerald-400">{simulationResult.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha</strong></span>
          </div>
        </div>

        {/* TAB 1: 3D Digital Twin View */}
        {activeTab === 'twin3d' && (
          <div className="space-y-6">
            <ThreeFieldViewer
              field={selectedField}
              simulation={simulationResult}
              currentDayIndex={currentDayIndex}
              onChangeDayIndex={setCurrentDayIndex}
            />

            {/* Quick Summary KPIs beneath 3D viewport */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-500 block">Etapa Fenológica</span>
                <strong className="text-emerald-300 font-mono text-sm">{currentDayRecord.stage} ({currentDayRecord.stageCode})</strong>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-500 block">Índice de Área Foliar (LAI)</span>
                <strong className="text-cyan-300 font-mono text-sm">{currentDayRecord.lai} m²/m²</strong>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-500 block">Humedad Suelo (0-30cm)</span>
                <strong className="text-blue-300 font-mono text-sm">{(currentDayRecord.soilMoistureTop * 100).toFixed(1)}% vol</strong>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                <span className="text-slate-500 block">Índice de Estrés Hídrico (CWSI)</span>
                <strong className={`font-mono text-sm ${currentDayRecord.cwsi > 0.45 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {currentDayRecord.cwsi.toFixed(2)}
                </strong>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: Dashboard & KPIs */}
        {activeTab === 'dashboard' && (
          <MainDashboard
            simulation={simulationResult}
            currentDayIndex={currentDayIndex}
            onSelectDayIndex={setCurrentDayIndex}
          />
        )}

        {/* TAB 3: Simulation & Climate Config */}
        {activeTab === 'config' && (
          <SimulationConfigPanel
            field={selectedField}
            config={simulationConfig}
            onChangeConfig={async (newCfg) => {
              setSimulationConfig(newCfg);
              try {
                const res = await simulateScenario(selectedField, newCfg);
                setSimulationResult(res);
              } catch (error) {
                console.error('Config simulation failed', error);
                setSimulationResult(runPINNSimulation(selectedField, newCfg));
              }
            }}
            onRunSimulation={executeSimulation}
            isLoading={isSimulating}
          />
        )}

        {/* TAB 4: What-If Studio */}
        {activeTab === 'whatif' && (
          <WhatIfStudio
            field={selectedField}
            baseConfig={simulationConfig}
          />
        )}

        {/* TAB 5: GIS Field Map Manager */}
        {activeTab === 'map' && (
          <FieldMapManager
            fields={fields}
            selectedField={selectedField}
            onSelectField={handleSelectField}
            onAddField={handleAddField}
            onDeleteField={handleDeleteField}
          />
        )}

        {/* TAB 6: Reports & Export */}
        {activeTab === 'reports' && (
          <ReportsModule
            simulation={simulationResult}
            currentUser={currentUser}
          />
        )}

        {/* TAB 7: MLOps & Model Registry */}
        {activeTab === 'mlops' && (
          <MLOpsDashboard />
        )}

        {/* TAB 8: Data Pipelines Ingestion */}
        {activeTab === 'pipelines' && (
          <DataPipelinesView />
        )}

        {/* TAB 9: User Management & RBAC */}
        {activeTab === 'users' && (
          <UserManagement
            currentUser={currentUser}
            onSwitchUser={setCurrentUser}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>CeresPINN: Physics-Informed Neural Network (Richards + Priestley-Taylor + CMIP6 Downscaling)</span>
          <span className="font-mono text-[11px]">Diseñado para Investigación Agronómica y Producción de Maíz Resiliente a Sequías</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
