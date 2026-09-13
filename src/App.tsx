import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
  Globe,
  ShieldCheck,
  Sun,
  Moon,
  RefreshCw
} from 'lucide-react';
import { useTheme } from './context/ThemeContext';
import { 
  Field, 
  SimulationConfig, 
  SimulationResult, 
  User,
  DailySimulationRecord 
} from './types';
import { 
  DEFAULT_FIELDS, 
  DEFAULT_SIMULATION_CONFIG, 
  DEMO_USERS 
} from './data/mockData';
import { simulateScenario, fetchDatabaseHealth, fetchFields, fetchUsers, getModelStatus } from './services/api';
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
import { ValidationReport } from './components/ValidationReport';

type ActiveTab = 
  | 'twin3d' 
  | 'dashboard' 
  | 'config' 
  | 'whatif' 
  | 'map' 
  | 'reports' 
  | 'mlops' 
  | 'pipelines' 
  | 'users'
  | 'validation';

export const App: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { t, i18n } = useTranslation();
  const [fields, setFields] = useState<Field[]>(DEFAULT_FIELDS);
  const [selectedField, setSelectedField] = useState<Field>(DEFAULT_FIELDS[0]);
  const [simulationConfig, setSimulationConfig] = useState<SimulationConfig>(DEFAULT_SIMULATION_CONFIG);
  const [activeTab, setActiveTab] = useState<ActiveTab>('twin3d');
  const [currentUser, setCurrentUser] = useState<User>(DEMO_USERS[0]);
  const [currentDayIndex, setCurrentDayIndex] = useState<number>(65); // Mid-season by default
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [dbHealth, setDbHealth] = useState<any>(null);
  const [modelOnline, setModelOnline] = useState<boolean>(true);
  const [previousYield, setPreviousYield] = useState<number | null>(null);

  // Load backend data (fields, users, model status, initial simulation) on mount
  useEffect(() => {
    let isMounted = true;

    const initAppData = async () => {
      try {
        const [fieldsRes, usersRes, healthRes, modelStatusRes] = await Promise.all([
          fetchFields(),
          fetchUsers(),
          fetchDatabaseHealth(),
          getModelStatus(),
        ]);

        if (isMounted) {
          if (!fieldsRes.fallback && fieldsRes.fields.length > 0) {
            setFields(fieldsRes.fields);
            setSelectedField(fieldsRes.fields[0]);
          }
          if (!usersRes.fallback && usersRes.users.length > 0) {
            setCurrentUser(usersRes.users[0]);
          }
          setDbHealth(healthRes.health);
          setModelOnline(modelStatusRes.status === 'ready' || !modelStatusRes.fallback);
          
          const initialField = (!fieldsRes.fallback && fieldsRes.fields.length > 0) 
            ? fieldsRes.fields[0] 
            : DEFAULT_FIELDS[0];
          try {
            const liveSim = await simulateScenario(initialField, DEFAULT_SIMULATION_CONFIG);
            if (isMounted) {
              setSimulationResult(liveSim);
            }
          } catch (e) {
            console.warn('Initial live simulation failed, keeping local fallback', e);
          }
        }
      } catch (error) {
        console.warn('Could not connect to FastAPI backend during mount; keeping offline fallbacks.', error);
      }
    };

    void initAppData();

    return () => {
      isMounted = false;
    };
  }, []);

  // Computed simulation result based on field and configuration
  const [simulationResult, setSimulationResult] = useState<SimulationResult>(() => 
    runPINNSimulation(DEFAULT_FIELDS[0], DEFAULT_SIMULATION_CONFIG)
  );

  // Sync currentDayRecord safely with active simulation result
  const currentDayRecord: DailySimulationRecord = 
    simulationResult.dailyRecords[currentDayIndex] || 
    simulationResult.dailyRecords[0] || {
      day: 1,
      dap: 1,
      date: '2026-05-15',
      gddAccumulated: 0,
      stage: 'Emergence',
      stageCode: 'VE',
      biomassKgHa: 45,
      lai: 0.1,
      rootDepthCm: 15,
      canopyHeightM: 0.2,
      soilMoistureTop: 0.24,
      soilMoistureMid: 0.28,
      soilMoistureDeep: 0.32,
      soilMoistureAvg: 0.28,
      etoMm: 3.2,
      etcMm: 1.1,
      transpirationMm: 0.8,
      evaporationMm: 0.3,
      precipitationMm: 0,
      irrigationMm: 0,
      runoffMm: 0,
      deepDrainageMm: 0,
      cwsi: 0.12,
      thermalStressFactor: 0.05,
      dailyYieldLossPotentialKgHa: 0,
      tempMaxC: 26.5,
      tempMinC: 14.2,
      solarRadiationMjM2: 21.5,
      vpdKpa: 1.1,
    };

  // Re-run simulation when field or config changes or user triggers run
  const executeSimulation = async () => {
    setIsSimulating(true);
    setPreviousYield(simulationResult.summaryKPIs.projectedYieldKgHa);
    try {
      const res = await simulateScenario(selectedField, simulationConfig);
      setSimulationResult(res);
      setModelOnline(true);
      if (currentDayIndex >= res.dailyRecords.length) {
        setCurrentDayIndex(res.dailyRecords.length - 1);
      }
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

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans flex flex-col selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navbar */}
      <header id="main-header" className="sticky top-0 z-50 bg-white/90 dark:bg-slate-950/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Scientific Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 via-emerald-500 to-teal-400 p-0.5 shadow-lg shadow-emerald-500/20 flex items-center justify-center">
              <div className="w-full h-full bg-white dark:bg-slate-950 rounded-[14px] flex items-center justify-center">
                <Sprout className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-black tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  CeresPINN
                  <span className="text-[11px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 font-bold">
                    v2.5
                  </span>
                  <span className="hidden md:inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-semibold border border-emerald-500/30 ml-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    FastAPI Modelo Conectado (R² 0.7842)
                  </span>
                </h1>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium hidden sm:block">
                {t('app.headerSubtitle')}
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
                className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold rounded-xl px-3 py-2 pr-8 focus:outline-none focus:border-emerald-500 cursor-pointer appearance-none"
              >
                {fields.map(f => (
                  <option key={f.id} value={f.id}>
                    📍 {f.name} ({f.areaHectares} ha)
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Theme toggle */}
            <button
              id="btn-theme-toggle"
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-all"
              title={theme === 'dark' ? t('app.themeToggleToLight') : t('app.themeToggleToDark')}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </button>

            {/* Language selector */}
            <div className="relative">
              <select
                onChange={(e) => {
                  const code = e.target.value;
                  i18n.changeLanguage(code);
                  localStorage.setItem('lang', code);
                }}
                value={i18n.language ?? 'es'}
                className="p-2 pl-8 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-all cursor-pointer appearance-none text-xs font-bold"
                title={t('app.langSelectorTitle')}
              >
                <option value="es">ES</option>
                <option value="en">EN</option>
                <option value="pt">PT</option>
              </select>
              <Globe className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Run button shortcut */}
            <button
              id="btn-quick-run-sim"
              onClick={executeSimulation}
              disabled={isSimulating}
              className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-600/30 transition-all disabled:opacity-50"
              title={t('app.quickRunTitle')}
            >
              <Zap className={`w-3.5 h-3.5 text-amber-300 ${isSimulating ? 'animate-spin' : ''}`} />
              <span className="hidden md:inline">{isSimulating ? t('app.quickRunExecuting') : t('app.quickRunLabel')}</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs Bar */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center gap-1 overflow-x-auto py-1 border-t border-slate-100 dark:border-slate-900 text-xs">
          <button
            id="tab-btn-twin3d"
            onClick={() => setActiveTab('twin3d')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'twin3d' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            {t('app.tabTwin3d')}
          </button>

          <button
            id="tab-btn-dashboard"
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'dashboard' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            {t('app.tabDashboard')}
          </button>

          <button
            id="tab-btn-config"
            onClick={() => setActiveTab('config')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'config' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            {t('app.tabConfig')}
          </button>

          <button
            id="tab-btn-whatif"
            onClick={() => setActiveTab('whatif')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'whatif' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            {t('app.tabWhatIf')}
          </button>

          <button
            id="tab-btn-map"
            onClick={() => setActiveTab('map')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'map' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <MapPin className="w-3.5 h-3.5" />
            {t('app.tabMap')}
          </button>

          <button
            id="tab-btn-reports"
            onClick={() => setActiveTab('reports')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'reports' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            {t('app.tabReports')}
          </button>

          <button
            id="tab-btn-mlops"
            onClick={() => setActiveTab('mlops')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'mlops' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            {t('app.tabMlOps')}
          </button>

          <button
            id="tab-btn-pipelines"
            onClick={() => setActiveTab('pipelines')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'pipelines' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            {t('app.tabPipelines')}
          </button>

          <button
            id="tab-btn-users"
            onClick={() => setActiveTab('users')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'users' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            {t('app.tabUsers')}
          </button>

          <button
            id="tab-btn-validation"
            onClick={() => setActiveTab('validation')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'validation' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-slate-200 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            {t('app.tabValidation')}
          </button>
        </div>
      </header>

      {/* Main App Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Status Sub-Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-slate-100/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800/80 text-xs">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-slate-600 dark:text-slate-400">
              {t('app.statusBarField')} <strong className="text-slate-800 dark:text-slate-200">{selectedField.name}</strong> ({selectedField.locationName})
            </span>
            <span className="text-slate-600 dark:text-slate-400">
              {t('app.statusBarUser')} <strong className="text-slate-800 dark:text-slate-200">{currentUser.name}</strong> ({currentUser.role})
            </span>
            <span className="text-slate-600 dark:text-slate-400">
              {t('app.statusBarScenario')} <strong className="text-slate-800 dark:text-slate-200">{simulationConfig.scenario}</strong>
            </span>
          </div>
          <div className="flex items-center gap-3">
            {dbHealth && (
              <div className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-cyan-500 dark:text-cyan-400" />
                <span className="text-slate-600 dark:text-slate-400">{t('app.statusBarDb')}</span>
                <span className={`px-2 py-1 rounded-lg font-mono text-[11px] ${
                  dbHealth.status === 'healthy' || dbHealth.status === 'connected' ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40' : 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/40'
                }`}>
                  {dbHealth.status === 'healthy' || dbHealth.status === 'connected' ? t('app.statusBarOk') : t('app.statusBarMock')}
                </span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <span className="text-slate-600 dark:text-slate-400">{t('app.statusBarStatus')}</span>
              <span className={`px-2 py-1 rounded-lg font-mono text-[11px] ${
                isSimulating ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/40' : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40'
              }`}>
                {isSimulating ? t('app.statusBarSimulating') : t('app.statusBarReady')}
              </span>
            </div>
          </div>
        </div>

        {/* TAB 1: 3D Twin & Phenology */}
        {activeTab === 'twin3d' && (
          <div className="space-y-6">
            {/* Descriptive Module Header for Gemelo 3D */}
            <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-cyan-950/30 border border-emerald-500/30 shadow-xl space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Sprout className="w-6 h-6 text-emerald-400" />
                    <h2 className="text-xl font-black text-slate-100 tracking-tight">
                      Gemelo Digital 3D & Dinámica Fenológica (Zea mays L.)
                    </h2>
                  </div>
                  <p className="text-xs text-slate-300 max-w-3xl">
                    <strong>¿Para qué sirve?</strong> Visualiza la evolución del cultivo en 3D acoplada a la física de Richards (3 capas de suelo) y forzamiento climático CMIP6.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1.5 rounded-xl bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 text-xs font-mono font-bold">
                    Ciclo Simulado: {simulationResult.dailyRecords.length} días
                  </span>
                </div>
              </div>
            </div>

            {/* Essential Controls Bar directly in 3D Twin */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-500" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                    Configuración Esencial del Cultivo & Clima
                  </h3>
                </div>
                <span className="text-[11px] text-slate-500">
                  Modifica las variables y pulsa <strong>"Aplicar y Re-ejecutar PINN"</strong> para ver los cambios instantáneos
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                {/* Variedad de Maíz */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-bold mb-1.5">
                    Variedad de Maíz (Días de Ciclo)
                  </label>
                  <select
                    id="select-twin-variety"
                    value={simulationConfig.maizeVariety}
                    onChange={(e) => setSimulationConfig(prev => ({ ...prev, maizeVariety: e.target.value as any }))}
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-medium text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="short_cycle">⚡ Ciclo Corto (~95 días - Escape Sequía)</option>
                    <option value="medium_cycle">🌽 Ciclo Medio (~115 días - Balanceado)</option>
                    <option value="long_cycle">🌾 Ciclo Largo (~135 días - Alto Potencial)</option>
                  </select>
                </div>

                {/* Estrategia de Riego */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-bold mb-1.5">
                    Estrategia de Riego
                  </label>
                  <select
                    id="select-twin-irrigation"
                    value={simulationConfig.irrigationStrategy}
                    onChange={(e) => setSimulationConfig(prev => ({ ...prev, irrigationStrategy: e.target.value as any }))}
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-medium text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="rainfed">🌧️ Secano Estricto (Temporal)</option>
                    <option value="deficit_50">💧 Déficit Controlado (50%)</option>
                    <option value="deficit_75">💧 Déficit Moderado (75%)</option>
                    <option value="optimal_100">💦 Riego Óptimo (100% ETc)</option>
                    <option value="smart_sensor">📡 Sensores Inteligentes</option>
                  </select>
                </div>

                {/* Escenario Climático CMIP6 */}
                <div>
                  <label className="block text-slate-600 dark:text-slate-400 font-bold mb-1.5">
                    Escenario Climático CMIP6
                  </label>
                  <select
                    id="select-twin-scenario"
                    value={simulationConfig.scenario}
                    onChange={(e) => {
                      const sc = e.target.value as any;
                      const anom = sc === 'SSP1-2.6' ? 0.9 : sc === 'SSP5-8.5' ? 2.6 : 1.8;
                      const precip = sc === 'SSP1-2.6' ? -2.0 : sc === 'SSP5-8.5' ? -25.0 : -12.0;
                      setSimulationConfig(prev => ({ 
                        ...prev, 
                        scenario: sc,
                        temperatureAnomalyC: anom,
                        precipitationAnomalyPercent: precip
                      }));
                    }}
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-medium text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="SSP1-2.6">🟢 SSP1-2.6 (Sostenible +0.9°C)</option>
                    <option value="SSP3-7.0">🟡 SSP3-7.0 (Intermedio +1.8°C)</option>
                    <option value="SSP5-8.5">🔴 SSP5-8.5 (Fósil Extremo +2.6°C)</option>
                  </select>
                </div>

                {/* Botón de Ejecución Directa */}
                <div className="flex flex-col justify-end">
                  <button
                    id="btn-apply-twin-config"
                    onClick={executeSimulation}
                    disabled={isSimulating}
                    className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50 cursor-pointer"
                  >
                    {isSimulating ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Simulando CeresPINN...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 text-amber-300" />
                        ⚡ Aplicar y Re-ejecutar PINN
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Tarjeta de Resultados Rápidos con Comparación */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-emerald-500/20 flex flex-wrap items-center justify-between gap-4 text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Rendimiento CeresPINN Calculado</span>
                    <strong className="text-slate-900 dark:text-slate-100 font-mono text-base">
                      {simulationResult.summaryKPIs.projectedYieldKgHa.toLocaleString()} kg/ha
                    </strong>
                  </div>
                  {previousYield !== null && previousYield !== simulationResult.summaryKPIs.projectedYieldKgHa && (
                    <span className={`px-2 py-1 rounded-lg font-mono text-xs font-bold flex items-center ${
                      simulationResult.summaryKPIs.projectedYieldKgHa > previousYield
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                    }`}>
                      {simulationResult.summaryKPIs.projectedYieldKgHa > previousYield ? '+' : ''}
                      {(simulationResult.summaryKPIs.projectedYieldKgHa - previousYield).toLocaleString()} kg/ha
                      {' '}({((simulationResult.summaryKPIs.projectedYieldKgHa - previousYield) / previousYield * 100).toFixed(1)}%)
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-3 text-slate-600 dark:text-slate-400 font-mono text-xs">
                  <span>Ciclo Total: <strong className="text-emerald-600 dark:text-emerald-400">{simulationResult.dailyRecords.length} días</strong></span>
                  <span>Cosecha (R6): <strong className="text-slate-800 dark:text-slate-200">DAP {simulationResult.summaryKPIs.daysToMaturity}</strong></span>
                  <span>Estrés Pico: <strong className={simulationResult.summaryKPIs.peakWaterStressIndex > 0.5 ? "text-rose-500 font-bold" : "text-emerald-500"}>{simulationResult.summaryKPIs.peakWaterStressIndex} CWSI</strong></span>
                  <span>Agua Consumida: <strong className="text-blue-500">{simulationResult.summaryKPIs.totalWaterConsumedMm} mm</strong></span>
                  <span className="bg-emerald-500/10 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-md border border-emerald-500/30 text-[11px]">
                    Día en 3D: <strong>DAP {currentDayIndex + 1} ({currentDayRecord.stage})</strong>
                  </span>
                </div>
              </div>
            </div>

            <ThreeFieldViewer
              field={selectedField}
              simulation={simulationResult}
              currentDayIndex={currentDayIndex}
              onChangeDayIndex={setCurrentDayIndex}
            />

            {/* Quick Summary KPIs beneath 3D viewport */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-xs shadow-sm">
                <span className="text-slate-500 dark:text-slate-500 block">{t('app.kpiPhenologicalStage')}</span>
                <strong className="text-emerald-600 dark:text-emerald-300 font-mono text-sm">{currentDayRecord.stage} ({currentDayRecord.stageCode})</strong>
              </div>
              <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-xs shadow-sm">
                <span className="text-slate-500 dark:text-slate-500 block">{t('app.kpiLai')}</span>
                <strong className="text-cyan-600 dark:text-cyan-300 font-mono text-sm">{currentDayRecord.lai} m²/m²</strong>
              </div>
              <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-xs shadow-sm">
                <span className="text-slate-500 dark:text-slate-500 block">{t('app.kpiSoilMoisture')}</span>
                <strong className="text-blue-600 dark:text-blue-300 font-mono text-sm">{(currentDayRecord.soilMoistureTop * 100).toFixed(1)}% vol</strong>
              </div>
              <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-xs shadow-sm">
                <span className="text-slate-500 dark:text-slate-500 block">{t('app.kpiCwsi')}</span>
                <strong className={`font-mono text-sm ${currentDayRecord.cwsi > 0.45 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
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

        {/* TAB 10: Statistical Validation */}
        {activeTab === 'validation' && (
          <ValidationReport />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-900 bg-white dark:bg-slate-950 py-4 text-center text-xs text-slate-500 dark:text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>{t('app.footerTitle')}</span>
          <span className="font-mono text-[11px]">{t('app.footerSubtitle')}</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
