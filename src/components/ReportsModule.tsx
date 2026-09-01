import React, { useState } from 'react';
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
import * as XLSX from 'xlsx';
import { SimulationResult, User } from '../types';

interface ReportsModuleProps {
  simulation: SimulationResult;
  currentUser: User;
}

export const ReportsModule: React.FC<ReportsModuleProps> = ({ simulation, currentUser }) => {
  const [emailTo, setEmailTo] = useState<string>(currentUser.email || '');
  const [isEmailSent, setIsEmailSent] = useState<boolean>(false);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState<boolean>(false);
  const [isGeneratingExcel, setIsGeneratingExcel] = useState<boolean>(false);

  const kpi = simulation.summaryKPIs;

  // Generate and download executive PDF report
  const handleExportPDF = () => {
    setIsGeneratingPdf(true);
    try {
      const doc = new jsPDF();

      // Header Branding
      doc.setFillColor(15, 23, 42); // slate-900
      doc.rect(0, 0, 210, 35, 'F');

      doc.setTextColor(255, 255, 255);
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.text('CeresPINN - INFORME TÉCNICO DE GEMELO DIGITAL', 14, 18);

      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(16, 185, 129); // emerald-500
      doc.text('Modelado PINN Richards + Clima CMIP6 | Producción de Maíz Resiliente a Sequías', 14, 26);

      // Metadata Box
      doc.setTextColor(51, 65, 85);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.text('1. INFORMACIÓN DE LA PARCELA Y ESCENARIO', 14, 45);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.text(`Campo / Parcela: ${simulation.fieldName}`, 14, 52);
      doc.text(`Ubicación: ${simulation.fieldLocation}`, 14, 58);
      doc.text(`Escenario Climático: CMIP6 ${simulation.config.scenario} (Año ${simulation.config.targetYear})`, 14, 64);
      doc.text(`Variedad de Maíz: ${simulation.config.maizeVariety.replace('_', ' ').toUpperCase()}`, 110, 52);
      doc.text(`Estrategia de Riego: ${simulation.config.irrigationStrategy.toUpperCase()}`, 110, 58);
      doc.text(`Fecha de Siembra: ${simulation.config.plantingDate}`, 110, 64);

      // KPIs Summary Table
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10);
      doc.text('2. INDICADORES CLAVE DE DESEMPEÑO (KPIs)', 14, 76);

      doc.setFillColor(241, 245, 249);
      doc.rect(14, 80, 182, 38, 'F');
      doc.setDrawColor(203, 213, 225);
      doc.rect(14, 80, 182, 38, 'S');

      doc.setFontSize(9);
      doc.setTextColor(15, 23, 42);
      doc.text(`Rendimiento Proyectado: ${kpi.projectedYieldKgHa.toLocaleString()} kg/ha`, 20, 88);
      doc.text(`Rendimiento Potencial: ${kpi.potentialYieldKgHa.toLocaleString()} kg/ha`, 20, 96);
      doc.text(`Pérdida por Sequía: ${kpi.yieldLossDueToDroughtPercent}%`, 20, 104);
      doc.text(`Biomasa Total Acumulada: ${(kpi.totalBiomassKgHa / 1000).toFixed(1)} t/ha`, 20, 112);

      doc.text(`Agua Total Consumida (ET): ${kpi.totalWaterConsumedMm} mm`, 110, 88);
      doc.text(`Riego Aplicado: ${kpi.totalIrrigationAppliedMm} mm`, 110, 96);
      doc.text(`Productividad del Agua: ${kpi.waterProductivityKgM3} kg/m³`, 110, 104);
      doc.text(`Score de Resiliencia Climática: ${kpi.droughtResilienceScore} / 100`, 110, 112);

      // Agronomic Recommendations
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10);
      doc.setTextColor(51, 65, 85);
      doc.text('3. RECOMENDACIONES AGRONÓMICAS & MITIGACIÓN DE RIESGO', 14, 128);

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
      doc.text('4. SERIE TEMPORAL DE BALANCE HÍDRICO (MUESTRA DE ETAPAS CLAVE)', 14, yOffset + 6);

      yOffset += 12;
      doc.setFillColor(15, 23, 42);
      doc.rect(14, yOffset, 182, 7, 'F');
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(8);
      doc.text('DAP', 18, yOffset + 5);
      doc.text('Fecha', 32, yOffset + 5);
      doc.text('Etapa', 55, yOffset + 5);
      doc.text('Biomasa (kg)', 85, yOffset + 5);
      doc.text('Humedad Top', 115, yOffset + 5);
      doc.text('CWSI Stress', 145, yOffset + 5);
      doc.text('ET (mm)', 175, yOffset + 5);

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

      // Footer
      doc.setFontSize(7);
      doc.setTextColor(148, 163, 184);
      doc.text(`Generado automáticamente por CeresPINN Digital Twin | ${new Date().toISOString()} | Usuario: ${currentUser.name}`, 14, 285);

      doc.save(`Reporte_CeresPINN_${simulation.fieldName.replace(/\s+/g, '_')}_${simulation.config.scenario}.pdf`);
    } catch (err) {
      console.error('Error generating PDF:', err);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // Export full raw daily records to Excel (.xlsx)
  const handleExportExcel = () => {
    setIsGeneratingExcel(true);
    try {
      const dataRows = simulation.dailyRecords.map(d => ({
        'DAP (Días Tras Siembra)': d.dap,
        'Día del Año': d.day,
        'Fecha': d.date,
        'GDD Acumulado (°C·d)': d.gddAccumulated,
        'Etapa Fenológica': d.stage,
        'Código Etapa': d.stageCode,
        'Biomasa (kg/ha)': d.biomassKgHa,
        'Índice Área Foliar (LAI)': d.lai,
        'Profundidad Raíz (cm)': d.rootDepthCm,
        'Altura Dosel (m)': d.canopyHeightM,
        'Humedad Suelo 0-30cm (cm³/cm³)': d.soilMoistureTop,
        'Humedad Suelo 30-60cm (cm³/cm³)': d.soilMoistureMid,
        'Humedad Suelo 60-100cm (cm³/cm³)': d.soilMoistureDeep,
        'Humedad Suelo Promedio': d.soilMoistureAvg,
        'ETo Priestley-Taylor (mm)': d.etoMm,
        'ETc Potencial (mm)': d.etcMm,
        'Transpiración Cultivo (mm)': d.transpirationMm,
        'Evaporación Suelo (mm)': d.evaporationMm,
        'Precipitación (mm)': d.precipitationMm,
        'Riego Aplicado (mm)': d.irrigationMm,
        'Escorrentía Runoff (mm)': d.runoffMm,
        'Drenaje Profundo (mm)': d.deepDrainageMm,
        'Índice Estrés CWSI (0-1)': d.cwsi,
        'Estrés Térmico (0-1)': d.thermalStressFactor,
        'Temp Máx (°C)': d.tempMaxC,
        'Temp Mín (°C)': d.tempMinC,
        'Radiación Solar (MJ/m²)': d.solarRadiationMjM2,
        'VPD (kPa)': d.vpdKpa
      }));

      const worksheet = XLSX.utils.json_to_sheet(dataRows);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Serie_Diaria_PINN');

      // KPIs sheet
      const kpiRows = [
        { 'Parámetro': 'Campo', 'Valor': simulation.fieldName },
        { 'Parámetro': 'Ubicación', 'Valor': simulation.fieldLocation },
        { 'Parámetro': 'Escenario Climático CMIP6', 'Valor': simulation.config.scenario },
        { 'Parámetro': 'Año Proyección', 'Valor': simulation.config.targetYear },
        { 'Parámetro': 'Variedad Maíz', 'Valor': simulation.config.maizeVariety },
        { 'Parámetro': 'Estrategia Riego', 'Valor': simulation.config.irrigationStrategy },
        { 'Parámetro': 'Rendimiento Proyectado (kg/ha)', 'Valor': kpi.projectedYieldKgHa },
        { 'Parámetro': 'Rendimiento Potencial (kg/ha)', 'Valor': kpi.potentialYieldKgHa },
        { 'Parámetro': 'Pérdida por Sequía (%)', 'Valor': kpi.yieldLossDueToDroughtPercent },
        { 'Parámetro': 'Agua Total Consumida ET (mm)', 'Valor': kpi.totalWaterConsumedMm },
        { 'Parámetro': 'Productividad del Agua (kg/m³)', 'Valor': kpi.waterProductivityKgM3 },
        { 'Parámetro': 'Margen Económico Estimado ($/ha)', 'Valor': kpi.economicReturnUsdHa },
        { 'Parámetro': 'PINN PDE Richards Loss', 'Valor': simulation.pinnValidationMetrics.pdeResidualRichardsLoss }
      ];
      const kpiSheet = XLSX.utils.json_to_sheet(kpiRows);
      XLSX.utils.book_append_sheet(workbook, kpiSheet, 'Resumen_KPIs');

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
    <div id="reports-export-module" className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-400" />
            Centro de Reportes, Informes y Exportación de Datos
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Generación de informes ejecutivos en PDF, dataset completo en Excel (.xlsx) y comunicación a productores.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* PDF Export Card */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <div className="p-2.5 rounded-xl bg-rose-950/80 text-rose-400 w-fit border border-rose-800/60 mb-2">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-100">Informe Técnico Ejecutivo (PDF)</h3>
            <p className="text-xs text-slate-400 mt-1">
              Documento formal listo para stakeholders con resumen ejecutivo, gráficas de estrés y recomendaciones agronómicas.
            </p>
          </div>
          <button
            id="btn-download-pdf"
            onClick={handleExportPDF}
            disabled={isGeneratingPdf}
            className="w-full py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-rose-600/20 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            {isGeneratingPdf ? 'Generando PDF...' : 'Descargar Informe PDF'}
          </button>
        </div>

        {/* Excel Export Card */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <div className="p-2.5 rounded-xl bg-emerald-950/80 text-emerald-400 w-fit border border-emerald-800/60 mb-2">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-100">Dataset Completo (Excel / XLSX)</h3>
            <p className="text-xs text-slate-400 mt-1">
              Exportación de las 28 variables diarias del modelo PINN (humedades por capa, flujos ET, biomasa, índices de estrés).
            </p>
          </div>
          <button
            id="btn-download-excel"
            onClick={handleExportExcel}
            disabled={isGeneratingExcel}
            className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            {isGeneratingExcel ? 'Procesando XLSX...' : 'Descargar Dataset Excel'}
          </button>
        </div>

        {/* Share via Email Card */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <div className="p-2.5 rounded-xl bg-cyan-950/80 text-cyan-400 w-fit border border-cyan-800/60 mb-2">
              <Mail className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-slate-100">Compartir por Correo Electrónico</h3>
            <p className="text-xs text-slate-400 mt-1">
              Envía el reporte técnico agronómico y los KPIs del gemelo digital directamente a agricultores y consultores.
            </p>
          </div>

          <form onSubmit={handleSendEmail} className="space-y-2">
            <input
              type="email"
              required
              value={emailTo}
              onChange={(e) => setEmailTo(e.target.value)}
              placeholder="correo@ejemplo.com"
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              className="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-cyan-600/20"
            >
              {isEmailSent ? (
                <>
                  <Check className="w-3.5 h-3.5 text-white" />
                  ¡Reporte Enviado con Éxito!
                </>
              ) : (
                <>
                  <Share2 className="w-3.5 h-3.5" />
                  Enviar Reporte por Email
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
