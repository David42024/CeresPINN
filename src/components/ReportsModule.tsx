import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  FileText, 
  Download, 
  FileSpreadsheet, 
  Share2, 
  Mail, 
  Check, 
  Printer, 
  Copy,
  Sparkles,
  BookOpen
} from 'lucide-react';
import jsPDF from 'jspdf';
import { Bar, CartesianGrid, ComposedChart, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { SimulationResult, User } from '../types';
import { fetchReports } from '../services/api';
import { FigureExportToolbar } from './FigureExportToolbar';
import { FigureZoomControls, useFigureZoom } from './FigureZoomControls';
import { ExportDataTable } from './ExportDataTable';
import { createFigurePng, ExportRow, FigureExportOptions } from '../utils/figureExport';

interface ReportsModuleProps {
  simulation: SimulationResult;
  currentUser: User;
}

export const ReportsModule: React.FC<ReportsModuleProps> = ({ simulation, currentUser }) => {
  const { t } = useTranslation();
  const [emailTo, setEmailTo] = useState<string>(currentUser.email || '');
  const [isEmailSent, setIsEmailSent] = useState<boolean>(false);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState<boolean>(false);
  const [pdfExportError, setPdfExportError] = useState<string | null>(null);
  const [isGeneratingExcel, setIsGeneratingExcel] = useState<boolean>(false);
  const [reportsData, setReportsData] = useState<any>(null);
  const [loadingReports, setLoadingReports] = useState<boolean>(true);
  const biomassChartRef = useRef<HTMLDivElement>(null);
  const waterChartRef = useRef<HTMLDivElement>(null);
  const biomassZoom = useFigureZoom(simulation.dailyRecords);
  const waterZoom = useFigureZoom(simulation.dailyRecords);

  useEffect(() => {
    const loadReports = async () => {
      try {
        const data = await fetchReports();
        if (!data.fallback) {
          setReportsData(data.reports);
        }
      } catch (error) {
        console.warn('Failed to load reports, using fallback', error);
      } finally {
        setLoadingReports(false);
      }
    };
    
    loadReports();
  }, []);

  const kpi = simulation.summaryKPIs;
  const biomassFigure: FigureExportOptions = {
    title: t('reportFigures.biomassTitle'),
    interpretation: t('reportFigures.biomassInterpretation'),
    xAxisLabel: t('reportFigures.days'),
    yAxisLabel: t('reportFigures.biomassAxis'),
    fileName: 'cerespinn_reporte_biomasa_lai',
  };
  const waterFigure: FigureExportOptions = {
    title: t('reportFigures.waterTitle'),
    interpretation: t('reportFigures.waterInterpretation'),
    xAxisLabel: t('reportFigures.days'),
    yAxisLabel: t('reportFigures.waterAxis'),
    fileName: 'cerespinn_reporte_balance_hidrico',
  };
  const biomassRows: ExportRow[] = simulation.dailyRecords.map(day => ({
    DAP: day.dap,
    [t('reportFigures.biomass')]: day.biomassKgHa,
    [t('reportFigures.leafArea')]: day.lai,
  }));
  const waterRows: ExportRow[] = simulation.dailyRecords.map(day => ({
    DAP: day.dap,
    [t('reportFigures.precipitation')]: day.precipitationMm,
    [t('reportFigures.irrigation')]: day.irrigationMm,
    [t('reportFigures.eto')]: day.etoMm,
  }));

  // Generate and download executive PDF report
  const handleExportPDF = async () => {
    setIsGeneratingPdf(true);
    setPdfExportError(null);
    try {
      if (!biomassChartRef.current || !waterChartRef.current) {
        throw new Error('No se encontraron las figuras del reporte para exportarlas.');
      }
      const [biomassImage, waterImage] = await Promise.all([
        createFigurePng(biomassChartRef.current, biomassFigure),
        createFigurePng(waterChartRef.current, waterFigure),
      ]);
      const doc = new jsPDF();

      // Header Branding
      doc.setFillColor(15, 23, 42); // slate-900
      doc.rect(0, 0, 210, 35, 'F');

      doc.setTextColor(255, 255, 255);
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text(t('reportsModule.pdfHeader1'), 14, 18);

      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(16, 185, 129); // emerald-500
      doc.text(t('reportsModule.pdfHeader2'), 14, 26);

      // Metadata Box
      doc.setTextColor(51, 65, 85);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.text(t('reportsModule.pdfSec1'), 14, 45);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.text(`${t('reportsModule.pdfField')} ${simulation.fieldName}`, 14, 52);
      doc.text(`${t('reportsModule.pdfLocation')} ${simulation.fieldLocation}`, 14, 58);
      doc.text(`${t('reportsModule.pdfClimateScenario')} CMIP6 ${simulation.config.scenario} (Año ${simulation.config.targetYear})`, 14, 64);
      doc.text(`${t('reportsModule.pdfMaizeVariety')} ${simulation.config.maizeVariety.replace('_', ' ').toUpperCase()}`, 110, 52);
      doc.text(`${t('reportsModule.pdfIrrigationStrategy')} ${simulation.config.irrigationStrategy.toUpperCase()}`, 110, 58);
      doc.text(`${t('reportsModule.pdfPlantingDate')} ${simulation.config.plantingDate}`, 110, 64);

      // KPIs Summary Table
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10);
      doc.text(t('reportsModule.pdfSec2'), 14, 76);

      doc.setFillColor(241, 245, 249);
      doc.rect(14, 80, 182, 43, 'F');
      doc.setDrawColor(203, 213, 225);
      doc.rect(14, 80, 182, 43, 'S');

      doc.setFontSize(9);
      doc.setTextColor(15, 23, 42);
      if (kpi.rawModelYieldKgHa) {
        doc.text(`Rendimiento Bruto (ML): ${kpi.rawModelYieldKgHa.toLocaleString()} kg/ha`, 20, 86);
      }
      doc.text(`${t('reportsModule.pdfProjectedYield')} ${kpi.projectedYieldKgHa.toLocaleString()} kg/ha`, 20, 92);
      doc.setTextColor(16, 185, 129); // emerald-500
      doc.text(`Modelo: ${simulation.modelName} | Fuente: ${simulation.modelDataSource ?? 'sin metadata'}`, 20, 97);
      doc.setTextColor(15, 23, 42); // reset color
      doc.text(`${t('reportsModule.pdfPotentialYield')} ${kpi.potentialYieldKgHa.toLocaleString()} kg/ha`, 20, 104);
      doc.text(`${t('reportsModule.pdfDroughtLoss')} ${kpi.gapToHeuristicPotentialPercent}%`, 20, 111);
      doc.text(`${t('reportsModule.pdfTotalBiomass')} ${(kpi.totalBiomassKgHa / 1000).toFixed(1)} t/ha`, 20, 118);

      doc.text(`${t('reportsModule.pdfTotalWaterET')} ${kpi.totalWaterConsumedMm} mm`, 110, 88);
      doc.text(`${t('reportsModule.pdfIrrigationApplied')} ${kpi.totalIrrigationAppliedMm} mm`, 110, 96);
      doc.text(`${t('reportsModule.pdfWaterProductivity')} ${kpi.waterProductivityKgM3} kg/m³`, 110, 104);
      if (kpi.yieldAdjustmentComponents) {
        doc.text(`Multiplicadores: V=${kpi.yieldAdjustmentComponents.variety_mult} R=${kpi.yieldAdjustmentComponents.irrigation_mult} N=${kpi.yieldAdjustmentComponents.nitrogen_mult} C=${kpi.yieldAdjustmentComponents.co2_mult}`, 110, 111);
      }
      doc.text(`${t('reportsModule.pdfClimateScore')} ${kpi.droughtResilienceScore} / 100`, 110, 112);

      // Agronomic Recommendations
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10);
      doc.setTextColor(51, 65, 85);
      doc.text(t('reportsModule.pdfSec3'), 14, 128);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      let yOffset = 135;
      simulation.agronomicRecommendations.forEach((rec, idx) => {
        const cleanText = rec.replace(/\*\*/g, '');
        const splitText = doc.splitTextToSize(`• ${cleanText}`, 180);
        doc.text(splitText, 14, yOffset);
        yOffset += splitText.length * 5 + 3;
      });

      // Daily Data Excerpt
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10);
      doc.text(t('reportsModule.pdfSec4'), 14, yOffset + 6);

      yOffset += 12;
      doc.setFillColor(15, 23, 42);
      doc.rect(14, yOffset, 182, 7, 'F');
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(8);
      doc.text(t('reportsModule.pdfDAP'), 18, yOffset + 5);
      doc.text(t('reportsModule.pdfDate'), 32, yOffset + 5);
      doc.text(t('reportsModule.pdfStage'), 55, yOffset + 5);
      doc.text(t('reportsModule.pdfBiomassKg'), 85, yOffset + 5);
      doc.text(t('reportsModule.pdfMoistTop'), 115, yOffset + 5);
      doc.text(t('reportsModule.pdfCwsi'), 145, yOffset + 5);
      doc.text(t('reportsModule.pdfETmm'), 175, yOffset + 5);

      yOffset += 7;
      doc.setTextColor(30, 41, 59);
      const sampleDays = simulation.dailyRecords.filter((_, i) => i % 15 === 0 || i === simulation.dailyRecords.length - 1);
      sampleDays.forEach((d, i) => {
        if (i % 2 === 0) {
          doc.setFillColor(248, 250, 252);
          doc.rect(14, yOffset, 182, 6, 'F');
        }
        doc.text(String(d.dap), 18, yOffset + 4.5);
        doc.text(d.date, 32, yOffset + 4.5);
        doc.text(d.stageCode, 55, yOffset + 4.5);
        doc.text(String(d.biomassKgHa), 85, yOffset + 4.5);
        doc.text(`${(d.soilMoistureTop * 100).toFixed(1)}%`, 115, yOffset + 4.5);
        doc.text(String(d.cwsi), 145, yOffset + 4.5);
        doc.text(String(d.transpirationMm + d.evaporationMm), 175, yOffset + 4.5);
        yOffset += 6;
      });

      doc.addPage();
      doc.setTextColor(51, 65, 85);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(13);
      doc.text(`5. ${t('reportFigures.figures')}`, 14, 20);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.text(`1. ${biomassFigure.title}`, 14, 30);
      doc.addImage(biomassImage.dataUrl, 'PNG', 10, 34, 190, 190 * biomassImage.height / biomassImage.width);
      doc.addPage();
      doc.setTextColor(51, 65, 85);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.text(`2. ${waterFigure.title}`, 14, 20);
      doc.addImage(waterImage.dataUrl, 'PNG', 10, 24, 190, 190 * waterImage.height / waterImage.width);

      // Scientific scope is deliberately exported with every report so the
      // simulation cannot be detached from its decision-use limitations.
      doc.addPage();
      doc.setTextColor(51, 65, 85);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(13);
      doc.text(`6. ${t('scientificScope.title')}`, 14, 22);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(10);
      const scopeParagraphs = [
        t('scientificScope.badge'),
        t('scientificScope.summary'),
        t('scientificScope.limitSoil'),
        t('scientificScope.prohibited'),
        t('scientificScope.required'),
      ];
      let scopeY = 34;
      scopeParagraphs.forEach(paragraph => {
        const lines = doc.splitTextToSize(paragraph, 178);
        doc.text(lines, 16, scopeY);
        scopeY += lines.length * 6 + 5;
      });

      // Footer
      doc.setFontSize(7);
      doc.setTextColor(148, 163, 184);
      doc.text(`${t('reportsModule.pdfFooter')} | ${new Date().toISOString()} | ${t('reportsModule.pdfUser')} ${currentUser.name}`, 14, 285);

      doc.save(`Reporte_CeresPINN_${simulation.fieldName.replace(/\s+/g, '_')}_${simulation.config.scenario}.pdf`);
    } catch (err) {
      console.error('Error generating PDF:', err);
      setPdfExportError(err instanceof Error ? err.message : 'Error inesperado al generar el PDF.');
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // Export full raw daily records to Excel (.xlsx)
  const handleExportExcel = async () => {
    setIsGeneratingExcel(true);
    try {
      const XLSX = await import('xlsx');
      const dataRows = simulation.dailyRecords.map(d => ({
        [t('reportsModule.xlsxDAP')]: d.dap,
        [t('reportsModule.xlsxDay')]: d.day,
        [t('reportsModule.xlsxDate')]: d.date,
        [t('reportsModule.xlsxGDD')]: d.gddAccumulated,
        [t('reportsModule.xlsxStage')]: d.stage,
        [t('reportsModule.xlsxStageCode')]: d.stageCode,
        [t('reportsModule.xlsxBiomass')]: d.biomassKgHa,
        [t('reportsModule.xlsxLAI')]: d.lai,
        [t('reportsModule.xlsxRootDepth')]: d.rootDepthCm,
        [t('reportsModule.xlsxCanopy')]: d.canopyHeightM,
        [t('reportsModule.xlsxSoilTop')]: d.soilMoistureTop,
        [t('reportsModule.xlsxSoilMid')]: d.soilMoistureMid,
        [t('reportsModule.xlsxSoilDeep')]: d.soilMoistureDeep,
        [t('reportsModule.xlsxSoilAvg')]: d.soilMoistureAvg,
        [t('reportsModule.xlsxETo')]: d.etoMm,
        [t('reportsModule.xlsxETc')]: d.etcMm,
        [t('reportsModule.xlsxTranspCrop')]: d.transpirationMm,
        [t('reportsModule.xlsxEvapSoil')]: d.evaporationMm,
        [t('reportsModule.xlsxPrecip')]: d.precipitationMm,
        [t('reportsModule.xlsxIrrigation')]: d.irrigationMm,
        [t('reportsModule.xlsxRunoff')]: d.runoffMm,
        [t('reportsModule.xlsxDeepDrainage')]: d.deepDrainageMm,
        [t('reportsModule.xlsxCwsi')]: d.cwsi,
        [t('reportsModule.xlsxThermal')]: d.thermalStressFactor,
        [t('reportsModule.xlsxTMax')]: d.tempMaxC,
        [t('reportsModule.xlsxTMin')]: d.tempMinC,
        [t('reportsModule.xlsxSolarRad')]: d.solarRadiationMjM2,
        [t('reportsModule.xlsxVPD')]: d.vpdKpa
      }));

      const worksheet = XLSX.utils.json_to_sheet(dataRows);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, t('reportFigures.dailySheet'));

      // KPIs sheet
      const kpiRows = [
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiField'), [t('reportsModule.xlsxKpiValue')]: simulation.fieldName },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiLocation'), [t('reportsModule.xlsxKpiValue')]: simulation.fieldLocation },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiClimate'), [t('reportsModule.xlsxKpiValue')]: simulation.config.scenario },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiYear'), [t('reportsModule.xlsxKpiValue')]: simulation.config.targetYear },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiVariety'), [t('reportsModule.xlsxKpiValue')]: simulation.config.maizeVariety },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiIrrigation'), [t('reportsModule.xlsxKpiValue')]: simulation.config.irrigationStrategy },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiProjected'), [t('reportsModule.xlsxKpiValue')]: kpi.projectedYieldKgHa },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiPotential'), [t('reportsModule.xlsxKpiValue')]: kpi.potentialYieldKgHa },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiLoss'), [t('reportsModule.xlsxKpiValue')]: kpi.gapToHeuristicPotentialPercent },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiWater'), [t('reportsModule.xlsxKpiValue')]: kpi.totalWaterConsumedMm },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiProd'), [t('reportsModule.xlsxKpiValue')]: kpi.waterProductivityKgM3 },
        { [t('reportsModule.xlsxKpiParam')]: t('reportsModule.xlsxKpiMargin'), [t('reportsModule.xlsxKpiValue')]: kpi.economicReturnUsdHa },
        { [t('reportsModule.xlsxKpiParam')]: 'Modelo desplegado', [t('reportsModule.xlsxKpiValue')]: simulation.modelName },
        { [t('reportsModule.xlsxKpiParam')]: 'Fuente de entrenamiento', [t('reportsModule.xlsxKpiValue')]: simulation.modelDataSource ?? 'sin metadata' }
      ];
      const kpiSheet = XLSX.utils.json_to_sheet(kpiRows);
      XLSX.utils.book_append_sheet(workbook, kpiSheet, t('reportFigures.summarySheet'));

      const scopeRows = [
        { [t('reportFigures.aspect')]: t('reportFigures.classification'), [t('reportFigures.status')]: t('scientificScope.badge') },
        { [t('reportFigures.aspect')]: t('scientificScope.title'), [t('reportFigures.status')]: t('scientificScope.summary') },
        { [t('reportFigures.aspect')]: t('reportFigures.soil'), [t('reportFigures.status')]: t('scientificScope.limitSoil') },
        { [t('reportFigures.aspect')]: t('reportFigures.excludedUses'), [t('reportFigures.status')]: t('scientificScope.prohibited') },
        { [t('reportFigures.aspect')]: t('reportFigures.requirements'), [t('reportFigures.status')]: t('scientificScope.required') },
      ];
      const scopeSheet = XLSX.utils.json_to_sheet(scopeRows);
      XLSX.utils.book_append_sheet(workbook, scopeSheet, t('reportFigures.scopeSheet'));

      XLSX.writeFile(workbook, `Simulacion_CeresPINN_${simulation.fieldName.replace(/\s+/g, '_')}.xlsx`);
    } catch (err) {
      console.error('Error generating Excel:', err);
    } finally {
      setIsGeneratingExcel(false);
    }
  };

  const handleSendEmail = (e: React.FormEvent) => {
    e.preventDefault();
    setIsEmailSent(true);
    setTimeout(() => setIsEmailSent(false), 4000);
  };

  return (
    <div id="reports-export-module" className="bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            {t('reportsModule.title')}
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            {t('reportsModule.subtitle')}
          </p>
        </div>
      </div>

      <section className="space-y-4" aria-label={t('reportFigures.figures')}>
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('reportFigures.figures')}</h3>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{biomassFigure.title}</h4>
            <p className="text-xs text-slate-600 dark:text-slate-400">{biomassFigure.interpretation}</p>
            <FigureExportToolbar targetRef={biomassChartRef} options={biomassFigure} dataRows={biomassRows} />
            <FigureZoomControls {...biomassZoom} title={biomassFigure.title} />
            <div ref={biomassChartRef} className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={biomassZoom.records} margin={{ top: 8, right: 18, left: 8, bottom: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="dap" tick={{ fontSize: 11 }} minTickGap={18} label={{ value: biomassFigure.xAxisLabel, position: 'insideBottom', offset: -6, fontSize: 10 }} />
                  <YAxis yAxisId="biomass" tick={{ fontSize: 11 }} label={{ value: t('reportFigures.biomass'), angle: -90, position: 'insideLeft', fontSize: 10 }} />
                  <YAxis yAxisId="lai" tick={{ fontSize: 11 }} orientation="right" label={{ value: 'LAI (m²/m²)', angle: 90, position: 'insideRight', fontSize: 10 }} />
                  <Tooltip />
                  <Legend verticalAlign="top" wrapperStyle={{ fontSize: 11 }} />
                  <Line yAxisId="biomass" type="monotone" dataKey="biomassKgHa" name={t('reportFigures.biomass')} stroke="#059669" dot={false} isAnimationActive={false} />
                  <Line yAxisId="lai" type="monotone" dataKey="lai" name="LAI (m²/m²)" stroke="#0891b2" dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{waterFigure.title}</h4>
            <p className="text-xs text-slate-600 dark:text-slate-400">{waterFigure.interpretation}</p>
            <FigureExportToolbar targetRef={waterChartRef} options={waterFigure} dataRows={waterRows} />
            <FigureZoomControls {...waterZoom} title={waterFigure.title} />
            <div ref={waterChartRef} className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={waterZoom.records} margin={{ top: 8, right: 18, left: 8, bottom: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="dap" tick={{ fontSize: 11 }} minTickGap={18} label={{ value: waterFigure.xAxisLabel, position: 'insideBottom', offset: -6, fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} label={{ value: waterFigure.yAxisLabel, angle: -90, position: 'insideLeft', fontSize: 10 }} />
                  <Tooltip />
                  <Legend verticalAlign="top" wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="precipitationMm" name={t('reportFigures.precipitation')} fill="#0284c7" isAnimationActive={false} />
                  <Bar dataKey="irrigationMm" name={t('reportFigures.irrigation')} fill="#7c3aed" isAnimationActive={false} />
                  <Line dataKey="etoMm" name={t('reportFigures.eto')} stroke="#d97706" dot={false} isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        {pdfExportError && <p role="alert" className="text-xs text-rose-600 dark:text-rose-400">{pdfExportError}</p>}
      </section>

      <section aria-label={t('reportFigures.tables')} className="space-y-3">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('reportFigures.tables')}</h3>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <ExportDataTable title={t('reportFigures.biomassTable')} rows={biomassRows} fileName={biomassFigure.fileName} />
          <ExportDataTable title={t('reportFigures.waterTable')} rows={waterRows} fileName={waterFigure.fileName} />
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* PDF Export Card */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/80 text-rose-600 dark:text-rose-400 w-fit border border-rose-200 dark:border-rose-800/60 mb-2">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('reportsModule.pdfTitle')}</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              {t('reportsModule.pdfDesc')}
            </p>
          </div>
          <button
            id="btn-download-pdf"
            onClick={handleExportPDF}
            disabled={isGeneratingPdf}
            className="w-full py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-rose-600/20 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            {isGeneratingPdf ? t('reportsModule.btnGeneratingPdf') : t('reportsModule.btnDownloadPdf')}
          </button>
        </div>

        {/* Excel Export Card */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 w-fit border border-emerald-200 dark:border-emerald-800/60 mb-2">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('reportsModule.excelTitle')}</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              {t('reportsModule.excelDesc')}
            </p>
          </div>
          <button
            id="btn-download-excel"
            onClick={handleExportExcel}
            disabled={isGeneratingExcel}
            className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            {isGeneratingExcel ? t('reportsModule.btnGeneratingExcel') : t('reportsModule.btnDownloadExcel')}
          </button>
        </div>

        {/* Share via Email Card */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <div className="p-2.5 rounded-xl bg-cyan-50 dark:bg-cyan-950/80 text-cyan-600 dark:text-cyan-400 w-fit border border-cyan-200 dark:border-cyan-800/60 mb-2">
              <Mail className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">{t('reportsModule.emailTitle')}</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              {t('reportsModule.emailDesc')}
            </p>
          </div>

          <form onSubmit={handleSendEmail} className="space-y-2">
            <input
              type="email"
              required
              value={emailTo}
              onChange={(e) => setEmailTo(e.target.value)}
              placeholder={t('reportsModule.emailPlaceholder')}
              className="w-full px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              className="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-cyan-600/20"
            >
              {isEmailSent ? (
                <>
                  <Check className="w-3.5 h-3.5 text-white" />
                  {t('reportsModule.btnEmailSent')}
                </>
              ) : (
                <>
                  <Share2 className="w-3.5 h-3.5" />
                  {t('reportsModule.btnSendEmail')}
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
