import React, { useState } from 'react';
import { 
  MapPin, 
  Plus, 
  Download, 
  Upload, 
  Trash2, 
  Check, 
  Layers, 
  Compass, 
  FileText, 
  Info,
  Maximize2,
  Crop
} from 'lucide-react';
import { Field, SoilProfile } from '../types';
import { SOIL_PROFILES } from '../data/mockData';

interface FieldMapManagerProps {
  fields: Field[];
  selectedField: Field;
  onSelectField: (field: Field) => void;
  onAddField: (field: Field) => void;
  onDeleteField: (fieldId: string) => void;
}

export const FieldMapManager: React.FC<FieldMapManagerProps> = ({
  fields,
  selectedField,
  onSelectField,
  onAddField,
  onDeleteField
}) => {
  const [isCreatingField, setIsCreatingField] = useState<boolean>(false);
  const [newFieldName, setNewFieldName] = useState<string>('');
  const [newLocationName, setNewLocationName] = useState<string>('');
  const [newCountry, setNewCountry] = useState<string>('México');
  const [newArea, setNewArea] = useState<number>(50);
  const [newSoilKey, setNewSoilKey] = useState<string>('clay_loam');
  const [newCrop, setNewCrop] = useState<string>('Maíz Híbrido Grano');
  const [newAltitude, setNewAltitude] = useState<number>(850);
  const [mapZoom, setMapZoom] = useState<number>(1);
  const [geoJsonUploadError, setGeoJsonUploadError] = useState<string | null>(null);

  const handleCreateFieldSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFieldName) return;

    const baseLat = selectedField.centerLat + (Math.random() - 0.5) * 0.05;
    const baseLng = selectedField.centerLng + (Math.random() - 0.5) * 0.05;

    const newField: Field = {
      id: `field-${Date.now()}`,
      name: newFieldName,
      locationName: newLocationName || 'Región Agrícola',
      country: newCountry,
      centerLat: parseFloat(baseLat.toFixed(4)),
      centerLng: parseFloat(baseLng.toFixed(4)),
      areaHectares: newArea,
      altitudeMeters: newAltitude,
      currentCrop: newCrop,
      soilProfile: SOIL_PROFILES[newSoilKey] || SOIL_PROFILES.clay_loam,
      notes: 'Campo registrado por usuario con polígono georeferenciado.',
      polygon: {
        type: 'Polygon',
        coordinates: [
          [baseLat + 0.005, baseLng - 0.005],
          [baseLat + 0.005, baseLng + 0.005],
          [baseLat - 0.005, baseLng + 0.005],
          [baseLat - 0.005, baseLng - 0.005],
          [baseLat + 0.005, baseLng - 0.005]
        ]
      }
    };

    onAddField(newField);
    onSelectField(newField);
    setIsCreatingField(false);
    setNewFieldName('');
    setNewLocationName('');
  };

  const handleExportGeoJSON = () => {
    const geojsonData = {
      type: 'FeatureCollection',
      features: fields.map(f => ({
        type: 'Feature',
        properties: {
          id: f.id,
          name: f.name,
          location: f.locationName,
          country: f.country,
          areaHa: f.areaHectares,
          soilType: f.soilProfile.label,
          fieldCapacity: f.soilProfile.fieldCapacity,
          wiltingPoint: f.soilProfile.wiltingPoint,
          currentCrop: f.currentCrop
        },
        geometry: {
          type: 'Polygon',
          coordinates: [f.polygon.coordinates.map(c => [c[1], c[0]])] // [lng, lat] GeoJSON standard
        }
      }))
    };

    const blob = new Blob([JSON.stringify(geojsonData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `campos_agricolas_ceres_pinn_${Date.now()}.geojson`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImportGeoJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (parsed.type === 'FeatureCollection' && parsed.features?.length > 0) {
          const firstFeature = parsed.features[0];
          const coords = firstFeature.geometry.coordinates[0];
          const convertedCoords: [number, number][] = coords.map((pt: [number, number]) => [pt[1], pt[0]]);
          
          const importedField: Field = {
            id: `imported-${Date.now()}`,
            name: firstFeature.properties?.name || `Campo Importado ${file.name.replace('.geojson', '')}`,
            locationName: firstFeature.properties?.location || 'Área Importada',
            country: firstFeature.properties?.country || 'Internacional',
            centerLat: convertedCoords[0][0],
            centerLng: convertedCoords[0][1],
            areaHectares: firstFeature.properties?.areaHa || 45.0,
            altitudeMeters: 300,
            currentCrop: firstFeature.properties?.currentCrop || 'Maíz Grano',
            soilProfile: SOIL_PROFILES.clay_loam,
            polygon: {
              type: 'Polygon',
              coordinates: convertedCoords
            }
          };

          onAddField(importedField);
          onSelectField(importedField);
          setGeoJsonUploadError(null);
        } else {
          setGeoJsonUploadError('El archivo no contiene un FeatureCollection válido.');
        }
      } catch (err) {
        setGeoJsonUploadError('Error al procesar el archivo GeoJSON.');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div id="field-manager-module" className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-emerald-400" />
            Gestión Espacial y Polígonos de Campo
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Definición de coordenadas geográficas, propiedades hidrofísicas de suelo y perfiles PostGIS.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            id="btn-export-geojson"
            onClick={handleExportGeoJSON}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700 transition-all"
            title="Exportar polígonos a GeoJSON estándar"
          >
            <Download className="w-3.5 h-3.5" />
            Exportar GeoJSON
          </button>

          <label 
            id="btn-import-geojson"
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700 cursor-pointer transition-all"
          >
            <Upload className="w-3.5 h-3.5" />
            Importar Polígono
            <input type="file" accept=".geojson,.json" onChange={handleImportGeoJSON} className="hidden" />
          </label>

          <button
            id="btn-new-field-toggle"
            onClick={() => setIsCreatingField(!isCreatingField)}
            className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-md shadow-emerald-600/30 transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            Nuevo Campo
          </button>
        </div>
      </div>

      {geoJsonUploadError && (
        <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center justify-between">
          <span>{geoJsonUploadError}</span>
          <button onClick={() => setGeoJsonUploadError(null)} className="text-rose-400 font-bold">&times;</button>
        </div>
      )}

      {/* Modal / Inline Create Form */}
      {isCreatingField && (
        <form onSubmit={handleCreateFieldSubmit} className="p-4 rounded-xl bg-slate-950/80 border border-emerald-500/40 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-emerald-300 flex items-center gap-2">
              <Crop className="w-4 h-4" /> Registrar Nueva Parcela o Lote Agrícola
            </h3>
            <button
              type="button"
              onClick={() => setIsCreatingField(false)}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              Cancelar
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Nombre del Campo / Lote</label>
              <input
                type="text"
                required
                value={newFieldName}
                onChange={(e) => setNewFieldName(e.target.value)}
                placeholder="Ej. Parcela La Esperanza Lote 5"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Ubicación / Municipio</label>
              <input
                type="text"
                required
                value={newLocationName}
                onChange={(e) => setNewLocationName(e.target.value)}
                placeholder="Ej. Celaya, Guanajuato"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">País</label>
              <select
                value={newCountry}
                onChange={(e) => setNewCountry(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                <option value="México">México</option>
                <option value="Estados Unidos">Estados Unidos</option>
                <option value="Argentina">Argentina</option>
                <option value="Brasil">Brasil</option>
                <option value="España">España</option>
                <option value="Colombia">Colombia</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Área (Hectáreas)</label>
              <input
                type="number"
                min={1}
                max={5000}
                value={newArea}
                onChange={(e) => setNewArea(parseFloat(e.target.value) || 1)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Tipo de Suelo (Textura & Van Genuchten)</label>
              <select
                value={newSoilKey}
                onChange={(e) => setNewSoilKey(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                {Object.entries(SOIL_PROFILES).map(([k, s]) => (
                  <option key={k} value={k}>{s.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Cultivo / Variedad Inicial</label>
              <input
                type="text"
                value={newCrop}
                onChange={(e) => setNewCrop(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all shadow-md shadow-emerald-600/30"
            >
              Guardar y Seleccionar Campo
            </button>
          </div>
        </form>
      )}

      {/* Main Grid: Interactive Map Visualizer + Fields List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Saved Fields List & Metadata */}
        <div className="lg:col-span-5 space-y-3">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
            Campos Registrados ({fields.length})
          </div>

          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            {fields.map((field) => {
              const isSelected = field.id === selectedField.id;
              return (
                <div
                  key={field.id}
                  id={`field-card-${field.id}`}
                  onClick={() => onSelectField(field)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected 
                      ? 'bg-emerald-950/40 border-emerald-500 shadow-md shadow-emerald-950/50' 
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                        {field.name}
                        {isSelected && <span className="p-0.5 rounded-full bg-emerald-500 text-slate-950"><Check className="w-3 h-3" /></span>}
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">{field.locationName}, {field.country}</p>
                    </div>

                    {fields.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteField(field.id);
                        }}
                        className="p-1 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 transition-all"
                        title="Eliminar campo"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  {/* Metadata Chips */}
                  <div className="grid grid-cols-3 gap-2 mt-3 pt-2 border-t border-slate-800/80 text-[11px]">
                    <div className="bg-slate-900/80 p-1.5 rounded-lg border border-slate-800">
                      <span className="text-slate-500 block">Superficie</span>
                      <strong className="text-slate-200 font-mono">{field.areaHectares} ha</strong>
                    </div>
                    <div className="bg-slate-900/80 p-1.5 rounded-lg border border-slate-800">
                      <span className="text-slate-500 block">Suelo</span>
                      <strong className="text-emerald-400 truncate block">{field.soilProfile.label.split(' ')[0]}</strong>
                    </div>
                    <div className="bg-slate-900/80 p-1.5 rounded-lg border border-slate-800">
                      <span className="text-slate-500 block">Cap. Campo</span>
                      <strong className="text-cyan-400 font-mono">{(field.soilProfile.fieldCapacity * 100).toFixed(0)}% vol</strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Interactive High-Precision GIS Map Canvas */}
        <div className="lg:col-span-7 bg-slate-950 rounded-xl border border-slate-800 p-4 flex flex-col justify-between relative overflow-hidden min-h-[380px]">
          {/* Map Overlay Header */}
          <div className="flex items-center justify-between z-10">
            <div className="px-3 py-1 rounded-lg bg-slate-900/80 backdrop-blur-md border border-slate-800 text-xs font-mono text-slate-300">
              Coordenadas: {selectedField.centerLat.toFixed(4)}°N, {selectedField.centerLng.toFixed(4)}°W
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setMapZoom(Math.min(2.0, mapZoom + 0.2))}
                className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center justify-center text-sm font-bold"
              >
                +
              </button>
              <button
                onClick={() => setMapZoom(Math.max(0.6, mapZoom - 0.2))}
                className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center justify-center text-sm font-bold"
              >
                -
              </button>
            </div>
          </div>

          {/* SVG Map Canvas rendering satellite-style terrain and field boundary polygon */}
          <div className="relative flex-1 flex items-center justify-center my-2 select-none overflow-hidden">
            <svg 
              className="w-full h-64 transition-transform duration-300 ease-out" 
              viewBox="-120 -80 240 160"
              style={{ transform: `scale(${mapZoom})` }}
            >
              {/* Satellite Grid Texture Background */}
              <defs>
                <pattern id="grid-pattern" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1e293b" strokeWidth="0.5" />
                </pattern>
                <radialGradient id="field-glow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#047857" stopOpacity="0.05" />
                </radialGradient>
              </defs>

              <rect x="-120" y="-80" width="240" height="160" fill="#0b1120" />
              <rect x="-120" y="-80" width="240" height="160" fill="url(#grid-pattern)" />

              {/* Surrounding landscape parcels */}
              <polygon points="-90,-50 -30,-55 -25,-15 -85,-10" fill="#13231c" stroke="#1f3d2f" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
              <polygon points="-20,-55 60,-50 65,-10 -15,-15" fill="#1b2416" stroke="#2a3d20" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
              <polygon points="-85,0 -25,-5 -20,50 -80,55" fill="#201f16" stroke="#3d3720" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
              <polygon points="10,0 90,-5 85,55 15,50" fill="#152622" stroke="#204038" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />

              {/* Selected Field High-Resolution Polygon */}
              <polygon 
                points="-35,-25 35,-25 40,25 -30,25" 
                fill="url(#field-glow)" 
                stroke="#10b981" 
                strokeWidth="2.5" 
                className="transition-all duration-500"
              />

              {/* Vertices marker handles */}
              {[[-35,-25], [35,-25], [40,25], [-30,25]].map((pt, i) => (
                <circle key={i} cx={pt[0]} cy={pt[1]} r="3" fill="#34d399" stroke="#064e3b" strokeWidth="1.5" />
              ))}

              {/* Center Anchor Marker */}
              <g transform="translate(0, 0)">
                <circle r="4" fill="#10b981" className="animate-ping" opacity="0.75" />
                <circle r="3" fill="#ffffff" />
                <text y="-8" textAnchor="middle" fill="#f8fafc" fontSize="6" fontWeight="bold" fontFamily="sans-serif">
                  {selectedField.name}
                </text>
              </g>
            </svg>

            {/* Scale Bar */}
            <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-slate-900/90 border border-slate-800 text-[10px] font-mono text-slate-400 flex items-center gap-1">
              <div className="w-8 h-1 bg-emerald-500/80 rounded-sm"></div>
              <span>250 m</span>
            </div>
          </div>

          {/* Soil Physics Matrix Summary Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 border-t border-slate-800 text-xs">
            <div>
              <span className="text-slate-500 text-[11px] block">Materia Orgánica:</span>
              <strong className="text-slate-200 font-mono">{selectedField.soilProfile.organicMatterPercent}%</strong>
            </div>
            <div>
              <span className="text-slate-500 text-[11px] block">Densidad Aparente:</span>
              <strong className="text-slate-200 font-mono">{selectedField.soilProfile.bulkDensity} g/cm³</strong>
            </div>
            <div>
              <span className="text-slate-500 text-[11px] block">Cond. Saturada (Ks):</span>
              <strong className="text-cyan-400 font-mono">{selectedField.soilProfile.saturatedConductivityKs} mm/día</strong>
            </div>
            <div>
              <span className="text-slate-500 text-[11px] block">Agua Disponible:</span>
              <strong className="text-emerald-400 font-mono">
                {Math.round((selectedField.soilProfile.fieldCapacity - selectedField.soilProfile.wiltingPoint) * 1000)} mm/m
              </strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
