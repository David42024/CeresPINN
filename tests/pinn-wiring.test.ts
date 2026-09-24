import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const source = (relativePath: string) =>
  readFileSync(join(process.cwd(), relativePath), 'utf8');

test('all primary PINN execution buttons use the remote simulation handler', () => {
  const app = source('src/App.tsx');
  const config = source('src/components/SimulationConfig.tsx');

  assert.match(app, /id="btn-quick-run-sim"[\s\S]*?onClick=\{executeSimulation\}/);
  assert.match(app, /id="btn-apply-twin-config"[\s\S]*?onClick=\{executeSimulation\}/);
  assert.match(config, /id="btn-execute-simulation"[\s\S]*?onClick=\{onRunSimulation\}/);
  assert.match(config, /id="btn-execute-simulation-bottom"[\s\S]*?onClick=\{onRunSimulation\}/);
  assert.match(app, /onRunSimulation=\{executeSimulation\}/);
  assert.match(app, /const executeSimulation = async \(\) => \{[\s\S]*?simulateScenario\(selectedField, simulationConfig\)/);
});

test('scenario tools call the same backend PINN service', () => {
  for (const component of [
    'src/components/WhatIfStudio.tsx',
    'src/components/AdaptationPanel.tsx',
    'src/components/FieldScenarioComparison.tsx',
  ]) {
    const contents = source(component);
    assert.match(contents, /import \{ simulateScenario \} from ['"]\.\.\/services\/api['"]/);
    assert.match(contents, /simulateScenario\(/);
    assert.doesNotMatch(contents, /runPINNSimulation/);
  }
});

test('production simulation posts to FastAPI and rejects synthetic checkpoints', () => {
  const api = source('src/services/api.ts');

  assert.match(api, /fetch\(`\$\{API_BASE\}\/api\/simulate`/);
  assert.match(api, /method: 'POST'/);
  assert.match(api, /payload\?\.inference_mode !== 'pinn'/);
  assert.match(api, /payload\?\.model_uses_real_data !== true/);
  assert.match(api, /if \(REQUIRE_REMOTE_PINN\) \{\s*throw error;/);
});

test('chatbot uses the shared backend client and never embeds a Gemini key in the browser', () => {
  const widget = source('src/components/ChatbotWidget.tsx');
  const api = source('src/services/api.ts');

  assert.match(widget, /sendChatbotMessage\(trimmedMessage, context\)/);
  assert.doesNotMatch(widget, /context:\s*\{\s*simulationResult,\s*simulationConfig/);
  assert.match(api, /`\$\{API_BASE\}\/api\/chatbot`/);
  assert.match(api, /CHATBOT_TIMEOUT_MS/);
  assert.doesNotMatch(widget + api, /VITE_GEMINI_API_KEY|GEMINI_API_KEY/);
});

test('production UI and API contract omit legacy equation metrics and synthetic MLOps curves', () => {
  const files = [
    'backend/inference.py',
    'backend/app.py',
    'src/services/api.ts',
    'src/services/pinnEngine.ts',
    'src/types/index.ts',
    'src/components/MLOpsDashboard.tsx',
    'src/components/ReportsModule.tsx',
  ];
  const contents = files.map(source).join('\n');

  assert.doesNotMatch(contents, /pde_residual_richards_loss|boundary_condition_loss|physics_conservation_error_percent/i);
  assert.doesNotMatch(contents, /pdeResidualRichardsLoss|boundaryConditionLoss|physicsConservationErrorPercent/);
  assert.doesNotMatch(contents, /Richards|\bPDE\b|\bEDP\b/i);
  assert.doesNotMatch(contents, /lossHistoryData|epoch:\s*1000|boundaryLoss|pdeLoss/);
});

test('field comparison is explicitly exploratory rather than spatial validation', () => {
  const comparison = source('src/components/FieldScenarioComparison.tsx');

  assert.match(comparison, /no constituye una evaluación espacial validada/);
  assert.match(comparison, /Comparación Demostrativa de Campos/);
  assert.doesNotMatch(comparison, /Mapa de Vulnerabilidad|Recomendaciones de Política/);
});

test('ethics and equity limitations are enforced in API, UI, and exports', () => {
  const backend = source('backend/inference.py');
  const api = source('src/services/api.ts');
  const app = source('src/App.tsx');
  const notice = source('src/components/ScientificScopeNotice.tsx');
  const reports = source('src/components/ReportsModule.tsx');

  assert.match(backend, /"use_classification": "exploratory_research_only"/);
  assert.match(backend, /"soil_affects_yield_network": False/);
  assert.match(backend, /"territorial_prioritization_supported": False/);
  assert.match(api, /scientific_scope\?\.use_classification !== 'exploratory_research_only'/);
  assert.match(app, /<ScientificScopeNotice \/>/);
  assert.match(notice, /scientificScope\.prohibited/);
  assert.match(reports, /ÉTICA, EQUIDAD Y ALCANCE DE DECISIÓN/);
  assert.match(reports, /Alcance_cientifico/);
  assert.doesNotMatch(backend, /mitigar hasta 45%|Variedad recomendada|Adelantar fecha de siembra 12 días/);
});
