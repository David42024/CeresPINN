// Exercises the actual React controls and saves their downloads, without substituting data.
const { createRequire } = require('node:module');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const runtimeRequire = createRequire(process.env.CODEX_RUNTIME_PACKAGE || 'C:/Users/USERJSSV/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const { chromium } = runtimeRequire('playwright');
const XLSX = require('xlsx');

async function main() {
  const output = path.resolve('output');
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--no-proxy-server'], executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1920, height: 1200 } });
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  const errors = [];
  const failedRequests = [];
  const apiResponses = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('requestfailed', request => failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
  page.on('response', response => { if (response.url().includes('/api/')) apiResponses.push({ url: response.url(), status: response.status() }); });
  // Serve the actual production build through browser request interception. This
  // avoids Windows loopback restrictions; no application data is injected.
  const origin = 'http://cerespinn.local';
  const dist = path.resolve('dist');
  await page.route(`${origin}/**`, async route => {
    const url = new URL(route.request().url());
    const relative = decodeURIComponent(url.pathname).replace(/^\/+/, '') || 'index.html';
    const file = path.resolve(dist, relative);
    if (!file.startsWith(dist + path.sep)) return route.abort();
    try {
      const contentType = file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : file.endsWith('.html') ? 'text/html' : 'application/octet-stream';
      await route.fulfill({ body: await fs.readFile(file), contentType });
    } catch { await route.fulfill({ status: 404, body: 'Static file unavailable' }); }
  });
  const report = { date: new Date().toISOString(), url: origin, transport: 'Actual dist build served from disk through Playwright routing; application data is not injected.', dataSource: 'Built-in local simulation; backend not running. Backend inference is outside this validation.', figures: [], tables: [], errors, failedRequests, apiResponses };
  try {
    await page.goto(report.url, { waitUntil: 'domcontentloaded' });
    await page.locator('input[type=email]').fill('admin@agri.com');
    await page.locator('input[type=password]').fill('Ceres2026!');
    await page.locator('button[type=submit]').click();
    await page.locator('#tab-btn-reports').click();
    const module = page.locator('#reports-export-module');
    await module.locator('table').first().waitFor();
    assert.equal(await module.locator('table').count(), 2);
    assert.equal(await module.locator('.recharts-wrapper > svg.recharts-surface').count(), 2);
    report.scenario = (await page.locator('body').innerText()).slice(0, 2500);

    const titles = ['Desarrollo de biomasa e índice de área foliar', 'Balance hídrico diario del cultivo'];
    for (const title of titles) {
      const controls = module.getByRole('group', { name: `Zoom de ${title}`, exact: true });
      const chartCard = controls.locator('..');
      const xTicks = chartCard.locator('.recharts-xAxis-tick-labels .recharts-cartesian-axis-tick-value');
      const originalTicks = await xTicks.allTextContents();
      await controls.getByRole('button', { name: `Acercar ${title}`, exact: true }).click();
      await controls.getByText('2×', { exact: true }).waitFor();
      const zoomedTicks = await xTicks.allTextContents();
      assert.notDeepEqual(zoomedTicks, originalTicks, 'Zoom must change the visible time domain');
      await controls.getByRole('slider').focus();
      await page.keyboard.press('End');
      const pannedTicks = await xTicks.allTextContents();
      assert.notDeepEqual(pannedTicks, zoomedTicks, 'Pan must change the visible time domain');
      await controls.getByRole('button', { name: `Alejar ${title}`, exact: true }).click();
      await controls.getByText('1×', { exact: true }).waitFor();
      assert.deepEqual(await xTicks.allTextContents(), originalTicks);
      await controls.getByRole('button', { name: `Acercar ${title}`, exact: true }).click();
      await controls.getByRole('button', { name: `Restablecer ${title}`, exact: true }).click();
      assert.deepEqual(await xTicks.allTextContents(), originalTicks);
      const chartBounds = await chartCard.locator('.recharts-wrapper > svg.recharts-surface').boundingBox();
      const downloadPromise = page.waitForEvent('download', { timeout: 45000 });
      await module.getByRole('button', { name: `Exportar ${title} como PNG a 600 DPI`, exact: true }).click();
      const download = await downloadPromise;
      const fileName = download.suggestedFilename();
      const file = path.join(output, fileName);
      await download.saveAs(file);
      const png = await fs.readFile(file);
      const width = png.readUInt32BE(16), height = png.readUInt32BE(20);
      let dpiX, dpiY;
      for (let offset = 8; offset + 12 <= png.length;) {
        const length = png.readUInt32BE(offset);
        if (png.toString('ascii', offset + 4, offset + 8) === 'pHYs') {
          assert.equal(png[offset + 16], 1);
          dpiX = png.readUInt32BE(offset + 8) * 0.0254;
          dpiY = png.readUInt32BE(offset + 12) * 0.0254;
        }
        offset += length + 12;
      }
      assert.ok(Math.abs(dpiX - 600) < 0.03 && Math.abs(dpiY - 600) < 0.03, 'PNG must have true 600 dpi metadata');
      assert.ok(Math.abs(width - Math.round(chartBounds.width * 600 / 96)) < 8, 'PNG must be rasterized at 600 dpi');
      report.figures.push({ title, fileName, width, height, dpiX, dpiY, zoomIn: true, zoomOut: true, pan: true, reset: true, originalTicks, zoomedTicks });
    }

    const tables = module.locator('table');
    for (let i = 0; i < 2; i++) {
      const table = tables.nth(i);
      const expectedHeaders = await table.locator('thead th').allTextContents();
      const expectedCount = await table.locator('tbody tr').count();
      const downloadPromise = page.waitForEvent('download');
      await table.locator('xpath=ancestor::section[1]').getByRole('button', { name: 'Descargar Excel (.xlsx)', exact: true }).click();
      const download = await downloadPromise;
      const fileName = download.suggestedFilename();
      const file = path.join(output, fileName);
      await download.saveAs(file);
      const book = XLSX.readFile(file);
      const sheet = book.Sheets[book.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(sheet);
      assert.equal(rows.length, expectedCount);
      assert.deepEqual(Object.keys(rows[0]), expectedHeaders);
      for (const rowIndex of [0, Math.floor(rows.length / 2), rows.length - 1]) {
        const cells = await table.locator('tbody tr').nth(rowIndex).locator('td').allTextContents();
        assert.equal(rows[rowIndex].DAP, Number(cells[0]));
        for (let j = 1; j < expectedHeaders.length; j++) {
          const value = rows[rowIndex][expectedHeaders[j]];
          assert.equal(typeof value, 'number', 'Excel data must preserve numeric types');
          assert.equal(value.toLocaleString('es-PE', { maximumFractionDigits: 3 }), cells[j]);
        }
      }
      report.tables.push({ fileName, sheet: book.SheetNames[0], rows: rows.length, columns: expectedHeaders, numericValuesMatchUi: true });
    }
    assert.deepEqual(errors, []);
    await module.screenshot({ path: path.join(output, 'frontend_validado.png'), style: 'header { visibility: hidden !important; }' });
    await page.setViewportSize({ width: 390, height: 844 });
    await module.locator('table').first().waitFor();
    report.mobileOverflow = await module.evaluate(el => el.scrollWidth > el.clientWidth + 1);
    assert.equal(report.mobileOverflow, false, 'Report module must fit a mobile viewport');
    await module.screenshot({ path: path.join(output, 'frontend_movil.png'), style: 'header { visibility: hidden !important; }' });
    report.status = 'PASS';
    await fs.writeFile(path.join(output, 'validacion.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    report.status = 'FAIL';
    report.failure = error.stack;
    await fs.writeFile(path.join(output, 'validacion.json'), JSON.stringify(report, null, 2));
    await page.screenshot({ path: path.join(output, 'error_validacion.png'), fullPage: true });
    await fs.writeFile(path.join(output, 'error_dom.html'), await page.content());
    console.error(error);
    console.log((await page.locator('body').innerText()).slice(-6000));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
