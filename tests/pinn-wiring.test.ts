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
  assert.match(api, /payload\?\.model_verified !== true/);
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
  assert.match(reports, /scientificScope\.title/);
  assert.match(reports, /reportFigures\.scopeSheet/);
  assert.equal((reports.match(/t\('scientificScope\.limitSpatial'\)/g) ?? []).length, 2);
  for (const lang of ['es', 'en', 'pt']) {
    const translations = JSON.parse(source(`src/i18n/locales/${lang}.json`));
    for (const key of ['title', 'summary', 'limitSoil', 'prohibited', 'required']) {
      assert.ok(translations.scientificScope[key], `${lang} is missing scientificScope.${key}`);
    }
    assert.ok(translations.reportFigures.scopeSheet, `${lang} is missing the scope worksheet label`);
    assert.ok(translations.reportFigures.spatialScope, `${lang} is missing the geographic scope label`);
  }
  assert.doesNotMatch(backend, /mitigar hasta 45%|Variedad recomendada|Adelantar fecha de siembra 12 días/);
});

test('rolling baseline results match predictions and expose limitations in all languages', () => {
  const audit = JSON.parse(source('docs/q1_artifacts/revision_20261026/audit.json'));
  const rows = source('docs/q1_artifacts/revision_20261026/rolling_origin_predictions.csv').trim().split(/\r?\n/);
  const headers = rows.shift()!.split(',');
  const records = rows.map(line => Object.fromEntries(line.split(',').map((value, index) => [headers[index], Number(value)])));
  assert.equal(new Set(records.map(row => row.year)).size, 20);
  for (const model of ['monotonic_all', 'linear_all', 'ridge_all', 'mlp_all']) {
    const score = audit.national.scores.find((item: { model: string }) => item.model === model);
    const rmse = Math.sqrt(records.reduce((sum, row) => sum + (row[model] - row.observed) ** 2, 0) / records.length);
    assert.ok(Math.abs(rmse - score.rmse_kg_ha) < 0.001, `${model} differs from frozen predictions`);
    assert.equal(score.block_bootstrap_95_ci.rmse_kg_ha.length, 2);
  }
  assert.ok(audit.national.scores.find((item: { model: string }) => item.model === 'ridge_all').rmse_kg_ha <
    audit.national.scores.find((item: { model: string }) => item.model === 'monotonic_all').rmse_kg_ha);
  for (const lang of ['es', 'en', 'pt']) {
    const translations = JSON.parse(source(`src/i18n/locales/${lang}.json`));
    for (const key of ['scope', 'design', 'interpretation', 'effect', 'sobolScope']) {
      assert.ok(translations.baselineAudit[key], `${lang} is missing baselineAudit.${key}`);
    }
  }
  assert.doesNotMatch(source('src/components/WhatIfStudio.tsx'), /Resolviendo Tensores de EDPs Acopladas/i);
});
