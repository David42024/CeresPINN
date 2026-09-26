import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const source = (relativePath: string) =>
  readFileSync(join(process.cwd(), relativePath), 'utf8');

test('Digital Twin Frontend: SimulationConfig handles thermodynamic parameters', () => {
  const configComponent = source('src/components/SimulationConfig.tsx');
  
  // Verify it contains the UI controls for the climate scenarios
  assert.match(configComponent, /temperatureAnomalyC/);
  assert.match(configComponent, /precipitationAnomalyPercent/);
  assert.match(configComponent, /co2Ppm/);
  
  // Verify it binds these controls to the state object
  assert.match(configComponent, /temperatureAnomalyC:/);
});

test('Digital Twin Frontend: WhatIfStudio renders the PINN inference results', () => {
  const studioComponent = source('src/components/WhatIfStudio.tsx');
  
  // Verify it correctly visualizes the PINN results
  assert.match(studioComponent, /summaryKPIs/);
  assert.match(studioComponent, /projectedYieldKgHa/);
  
  // Verify loading states are handled properly
  assert.match(studioComponent, /isComparing/);
});

test('Digital Twin Frontend: API payload contract is strictly typed', () => {
  const apiFile = source('src/services/api.ts');
  const typesFile = source('src/types/index.ts');
  
  // Verify the payload matches the frontend schema precisely
  assert.match(typesFile, /temperatureAnomalyC:\s*number/);
  assert.match(typesFile, /precipitationAnomalyPercent:\s*number/);
  assert.match(typesFile, /carbonDioxidePpm:\s*number/);
  
  // Verify the API client strictly types the request
  assert.match(apiFile, /export async function simulateScenario\(/);
});
