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
  Moon
} from 'lucide-react';
import { useTheme } from './context/ThemeContext';
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
import { simulateScenario, fetchDatabaseHealth } from './services/api';
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

  // Load database health on mount
  useEffect(() => {
    const loadDbHealth = async () => {
      try {
        const health = await fetchDatabaseHealth();
        if (!health.fallback) {
          setDbHealth(health.health);
        }
      } catch (error) {
        console.error('Failed to load database health', error);
      }
    };
    
    loadDbHealth();
  }, []);

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
              aria-label={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
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
                className="p-2 pl-8 pr-8 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-all cursor-pointer appearance-none text-xs font-bold"
                title={t('app.langSelectorTitle')}
              >
                <option value="es">ES</option>
                <option value="en">EN</option>
                <option value="pt">PT</option>
              </select>
              <Globe className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none" />
              <ChevronDown className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
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
              activeTab === 'twin3d' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            {t('app.tabTwin3d')}
          </button>

          <button
            id="tab-btn-dashboard"
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'dashboard' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            {t('app.tabDashboard')}
          </button>

          <button
            id="tab-btn-config"
            onClick={() => setActiveTab('config')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'config' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            {t('app.tabConfig')}
          </button>

          <button
            id="tab-btn-whatif"
            onClick={() => setActiveTab('whatif')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'whatif' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            {t('app.tabWhatIf')}
          </button>

          <button
            id="tab-btn-map"
            onClick={() => setActiveTab('map')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'map' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <MapPin className="w-3.5 h-3.5" />
            {t('app.tabMap')}
          </button>

          <button
            id="tab-btn-reports"
            onClick={() => setActiveTab('reports')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'reports' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            {t('app.tabReports')}
          </button>

          <button
            id="tab-btn-mlops"
            onClick={() => setActiveTab('mlops')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'mlops' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            {t('app.tabMlOps')}
          </button>

          <button
            id="tab-btn-pipelines"
            onClick={() => setActiveTab('pipelines')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'pipelines' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            {t('app.tabPipelines')}
          </button>

          <button
            id="tab-btn-users"
            onClick={() => setActiveTab('users')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'users' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            {t('app.tabUsers')}
          </button>

          <button
            id="tab-btn-validation"
            onClick={() => setActiveTab('validation')}
            className={`px-3 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              activeTab === 'validation' ? 'bg-slate-100 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border-b-2 border-emerald-500 dark:border-emerald-400' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
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
              {t('app.statusBarScenario')} <strong className="text-slate-800 dark:text-slate-200">{simulationConfig.climateScenario}</strong>
            </span>
          </div>
          <div className="flex items-center gap-3">
            {dbHealth && (
              <div className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-cyan-500 dark:text-cyan-400" />
                <span className="text-slate-600 dark:text-slate-400">{t('app.statusBarDb')}</span>
                <span className={`px-2 py-1 rounded-lg font-mono text-[11px] ${
                  dbHealth.status === 'healthy' ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40' : 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/40'
                }`}>
                  {dbHealth.status === 'healthy' ? t('app.statusBarOk') : t('app.statusBarMock')}
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
