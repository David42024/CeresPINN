import React, { Dispatch, SetStateAction, useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Layers, 
  Eye, 
  Maximize2, 
  Compass, 
  Sun, 
  Droplets, 
  Thermometer, 
  Info,
  Calendar,
  Activity
} from 'lucide-react';
import { DailySimulationRecord, SimulationResult } from '../types';

interface ThreeFieldViewerProps {
  simulation: SimulationResult | null;
  currentDayIndex: number;
  onChangeDayIndex: Dispatch<SetStateAction<number>>;
}

type VisualLayerMode = 'soil_moisture' | 'biomass' | 'water_stress' | 'true_color';
type CameraViewMode = 'perspective' | 'top_down' | 'ground';

export const ThreeFieldViewer: React.FC<ThreeFieldViewerProps> = ({
  simulation,
  currentDayIndex,
  onChangeDayIndex
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Controls state
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [layerMode, setLayerMode] = useState<VisualLayerMode>('soil_moisture');
  const [cameraMode, setCameraMode] = useState<CameraViewMode>('perspective');
  const [selectedDepth, setSelectedDepth] = useState<'top' | 'mid' | 'deep'>('top');
  const [showWireframe, setShowWireframe] = useState<boolean>(false);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1);

  // Three.js instances ref
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const terrainMeshRef = useRef<THREE.Mesh | null>(null);
  const plantsGroupRef = useRef<THREE.Group | null>(null);
  const soilLayersGroupRef = useRef<THREE.Group | null>(null);
  const isDraggingRef = useRef<boolean>(false);
  const previousMousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const cameraAngleRef = useRef<{ theta: number; phi: number; radius: number }>({
    theta: Math.PI / 4,
    phi: Math.PI / 3,
    radius: 35
  });

  const dailyRecord: DailySimulationRecord | undefined = simulation?.dailyRecords[currentDayIndex];

  // Playback timer loop
  useEffect(() => {
    if (!isPlaying || !simulation) return;

    const interval = setInterval(() => {
      onChangeDayIndex((prev) => {
        if (prev >= simulation.dailyRecords.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 120 / speedMultiplier);

    return () => clearInterval(interval);
  }, [isPlaying, simulation, speedMultiplier, onChangeDayIndex]);

  // Initialize Three.js scene
  useEffect(() => {
    if (!containerRef.current || !canvasRef.current) return;

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 500;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x090d16);
    scene.fog = new THREE.FogExp2(0x090d16, 0.015);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    cameraRef.current = camera;
    updateCameraPosition();

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 1.6);
    sunLight.position.set(25, 40, 20);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 100;
    sunLight.shadow.camera.left = -25;
    sunLight.shadow.camera.right = 25;
    sunLight.shadow.camera.top = 25;
    sunLight.shadow.camera.bottom = -25;
    scene.add(sunLight);

    const skyLight = new THREE.HemisphereLight(0x87ceeb, 0x3d2817, 0.6);
    scene.add(skyLight);

    // Create 3D Terrain with slight topographic undulations
    const terrainGeo = new THREE.PlaneGeometry(30, 30, 48, 48);
    terrainGeo.rotateX(-Math.PI / 2);
    
    // Add realistic subtle agricultural furrow topology
    const posAttr = terrainGeo.attributes.position;
    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getZ(i);
      // Furrows in z direction + soft mound
      const furrow = Math.sin(x * 2.5) * 0.12;
      const mound = Math.sin(x * 0.15) * Math.cos(z * 0.15) * 0.4;
      posAttr.setY(i, furrow + mound);
    }
    terrainGeo.computeVertexNormals();

    const terrainMat = new THREE.MeshStandardMaterial({
      color: 0x2b3820,
      roughness: 0.85,
      metalness: 0.1,
      wireframe: showWireframe
    });
    const terrain = new THREE.Mesh(terrainGeo, terrainMat);
    terrain.receiveShadow = true;
    scene.add(terrain);
    terrainMeshRef.current = terrain;

    // Soil profile cross-section slice below ground
    const soilLayersGroup = new THREE.Group();
    const layerDepths = [
      { depth: -1.2, color: 0x3e2723, label: '0-30cm Topsoil' },
      { depth: -2.5, color: 0x2d1a10, label: '30-60cm Subsoil' },
      { depth: -4.0, color: 0x1f120a, label: '60-100cm Deep Horizon' }
    ];
    layerDepths.forEach((l, idx) => {
      const boxGeo = new THREE.BoxGeometry(30.2, 1.2, 0.4);
      const boxMat = new THREE.MeshStandardMaterial({
        color: l.color,
        roughness: 0.9,
        transparent: true,
        opacity: 0.9
      });
      const slice = new THREE.Mesh(boxGeo, boxMat);
      slice.position.set(0, l.depth, 15.2);
      soilLayersGroup.add(slice);
    });
    scene.add(soilLayersGroup);
    soilLayersGroupRef.current = soilLayersGroup;

    // Grid helper on outer boundary
    const grid = new THREE.GridHelper(30, 20, 0x10b981, 0x1e293b);
    grid.position.y = -0.05;
    scene.add(grid);

    // Maize crop group
    const plantsGroup = new THREE.Group();
    scene.add(plantsGroup);
    plantsGroupRef.current = plantsGroup;

    // Render loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current);
      }
    };
    animate();

    // Resize observer
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const newWidth = containerRef.current.clientWidth;
      const newHeight = containerRef.current.clientHeight;
      cameraRef.current.aspect = newWidth / newHeight;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(newWidth, newHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, []);

  // Update camera position helper
  const updateCameraPosition = () => {
    if (!cameraRef.current) return;
    const { theta, phi, radius } = cameraAngleRef.current;
    
    if (cameraMode === 'top_down') {
      cameraRef.current.position.set(0, 42, 0.001);
      cameraRef.current.lookAt(0, 0, 0);
    } else if (cameraMode === 'ground') {
      cameraRef.current.position.set(0, 1.8, 12);
      cameraRef.current.lookAt(0, 1.5, 0);
    } else {
      // Perspective Orbit
      const x = radius * Math.sin(phi) * Math.sin(theta);
      const y = radius * Math.cos(phi);
      const z = radius * Math.sin(phi) * Math.cos(theta);
      cameraRef.current.position.set(x, Math.max(2, y), z);
      cameraRef.current.lookAt(0, 1, 0);
    }
  };

  // Sync camera mode changes
  useEffect(() => {
    if (cameraMode === 'top_down') {
      cameraAngleRef.current.radius = 42;
    } else if (cameraMode === 'ground') {
      cameraAngleRef.current.radius = 12;
    } else {
      cameraAngleRef.current.radius = 35;
      cameraAngleRef.current.phi = Math.PI / 3.2;
      cameraAngleRef.current.theta = Math.PI / 4;
    }
    updateCameraPosition();
  }, [cameraMode]);

  // Re-render maize crop and terrain colors whenever dailyRecord or layerMode changes
  useEffect(() => {
    if (!plantsGroupRef.current || !terrainMeshRef.current || !dailyRecord) return;

    const plantsGroup = plantsGroupRef.current;
    const terrain = terrainMeshRef.current;

    // 1. Colorize Terrain based on Layer Mode
    const mat = terrain.material as THREE.MeshStandardMaterial;
    mat.wireframe = showWireframe;

    if (layerMode === 'soil_moisture') {
      // Moisture gradient: dry terracotta (0.10) to hydrated deep turquoise/emerald (0.38)
      const targetMoisture = 
        selectedDepth === 'top' ? dailyRecord.soilMoistureTop :
        selectedDepth === 'mid' ? dailyRecord.soilMoistureMid : dailyRecord.soilMoistureDeep;
      
      const normalizedMoisture = Math.max(0, Math.min(1, (targetMoisture - 0.10) / (0.35 - 0.10)));
      const dryColor = new THREE.Color(0xa36a3e); // Dry brown
      const wetColor = new THREE.Color(0x0f5d47); // Wet rich soil
      const fieldColor = dryColor.clone().lerp(wetColor, normalizedMoisture);
      mat.color = fieldColor;
    } else if (layerMode === 'water_stress') {
      // Stress: Green (0) -> Orange (0.5) -> Scorched Red/Crimson (1.0)
      const stress = dailyRecord.cwsi;
      const noStress = new THREE.Color(0x10b981);
      const highStress = new THREE.Color(0xef4444);
      mat.color = noStress.clone().lerp(highStress, stress);
    } else if (layerMode === 'biomass') {
      // Biomass density: dark soil to vibrant crop emerald
      const frac = Math.min(1, dailyRecord.biomassKgHa / 22000);
      const startC = new THREE.Color(0x27272a);
      const maxC = new THREE.Color(0x15803d);
      mat.color = startC.clone().lerp(maxC, frac);
    } else {
      mat.color = new THREE.Color(0x3f3529); // Standard loam
    }

    // 2. Procedural 3D Plant Generation according to Stage
    // Clear previous plants
    while (plantsGroup.children.length > 0) {
      const child = plantsGroup.children[0] as THREE.Mesh;
      if (child.geometry) child.geometry.dispose();
      plantsGroup.remove(child);
    }

    // Generate grid of plants (e.g. 10x10 sample area)
    const height = Math.max(0.15, dailyRecord.canopyHeightM);
    const plantColor = 
      dailyRecord.cwsi > 0.5 
        ? new THREE.Color(0xca8a04).lerp(new THREE.Color(0x991b1b), dailyRecord.cwsi * 0.8) // Yellow/Drought scorched
        : dailyRecord.stageCode === 'R6'
        ? new THREE.Color(0xd97706) // Golden harvest
        : new THREE.Color(0x22c55e); // Lush green

    const stemGeo = new THREE.CylinderGeometry(0.04, 0.08, height, 6);
    stemGeo.translate(0, height / 2, 0);

    const leafGeo = new THREE.ConeGeometry(0.35 * Math.min(2.5, dailyRecord.lai), height * 0.4, 5);
    leafGeo.translate(0, height * 0.7, 0);

    const plantMaterial = new THREE.MeshStandardMaterial({
      color: plantColor,
      roughness: 0.6,
      metalness: 0.1
    });

    const rows = 12;
    const cols = 12;
    const spacingX = 2.2;
    const spacingZ = 2.2;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const posX = (r - rows / 2) * spacingX + (Math.sin(r * 3 + c) * 0.15);
        const posZ = (c - cols / 2) * spacingZ + (Math.cos(c * 2 + r) * 0.15);

        const plantMesh = new THREE.Mesh(stemGeo, plantMaterial);
        plantMesh.position.set(posX, 0, posZ);
        plantMesh.scale.set(
          1 + Math.sin(r + c) * 0.1,
          1 + Math.cos(r * 2 + c) * 0.1,
          1 + Math.sin(r + c) * 0.1
        );
        plantMesh.castShadow = true;

        // Add foliage leaves if past seedling stage
        if (dailyRecord.stageCode !== 'VE') {
          const foliage = new THREE.Mesh(leafGeo, plantMaterial);
          foliage.position.y = 0;
          foliage.rotation.y = (r * 37 + c * 19) % Math.PI;
          plantMesh.add(foliage);
        }

        // Tassels / Ears for reproductive stages (VT, R1, R3, R6)
        if (['VT', 'R1', 'R3', 'R6'].includes(dailyRecord.stageCode)) {
          const tasselGeo = new THREE.ConeGeometry(0.12, 0.35, 4);
          const tasselMat = new THREE.MeshStandardMaterial({
            color: dailyRecord.stageCode === 'R6' ? 0xb45309 : 0xfef08a
          });
          const tassel = new THREE.Mesh(tasselGeo, tasselMat);
          tassel.position.set(0, height, 0);
          plantMesh.add(tassel);
        }

        plantsGroup.add(plantMesh);
      }
    }
  }, [dailyRecord, layerMode, selectedDepth, showWireframe]);

  // Mouse drag Orbit Controls handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current || cameraMode !== 'perspective') return;

    const deltaX = e.clientX - previousMousePositionRef.current.x;
    const deltaY = e.clientY - previousMousePositionRef.current.y;

    cameraAngleRef.current.theta -= deltaX * 0.008;
    cameraAngleRef.current.phi = Math.max(0.1, Math.min(Math.PI / 2.05, cameraAngleRef.current.phi - deltaY * 0.008));

    updateCameraPosition();
    previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (cameraMode === 'top_down') {
      cameraAngleRef.current.radius = Math.max(15, Math.min(70, cameraAngleRef.current.radius + e.deltaY * 0.05));
    } else {
      cameraAngleRef.current.radius = Math.max(10, Math.min(65, cameraAngleRef.current.radius + e.deltaY * 0.04));
    }
    updateCameraPosition();
  };

  return (
    <div id="three-field-viewer-card" className="relative w-full h-[540px] bg-slate-900/90 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden flex flex-col select-none">
      {/* 3D Canvas Viewport */}
      <div 
        ref={containerRef}
        className="relative flex-1 w-full h-full cursor-grab active:cursor-grabbing overflow-hidden"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <canvas ref={canvasRef} className="w-full h-full block" />

        {/* Top Overlay Badges */}
        <div className="absolute top-4 left-4 z-10 flex flex-wrap items-center gap-2">
          <div className="px-3 py-1.5 rounded-xl bg-slate-950/80 backdrop-blur-md border border-slate-700/60 flex items-center gap-2 shadow-lg">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-semibold text-slate-200">
              Gemelo Digital 3D (Zea mays L.)
            </span>
          </div>

          {dailyRecord && (
            <div className="px-3 py-1.5 rounded-xl bg-emerald-950/70 backdrop-blur-md border border-emerald-700/50 text-emerald-300 text-xs font-medium flex items-center gap-1.5 shadow-lg">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              Etapa: <strong className="font-bold text-white">{dailyRecord.stage}</strong> ({dailyRecord.stageCode})
            </div>
          )}

          {dailyRecord && dailyRecord.cwsi > 0.40 && (
            <div className="px-3 py-1.5 rounded-xl bg-amber-950/80 backdrop-blur-md border border-amber-600/60 text-amber-300 text-xs font-medium flex items-center gap-1.5 shadow-lg animate-pulse">
              <Thermometer className="w-3.5 h-3.5 text-amber-400" />
              Estrés Hídrico: {(dailyRecord.cwsi * 100).toFixed(0)}%
            </div>
          )}
        </div>

        {/* Top Right: Layer Mode Selectors */}
        <div className="absolute top-4 right-4 z-10 flex flex-col items-end gap-2">
          <div className="p-1 rounded-xl bg-slate-950/85 backdrop-blur-md border border-slate-800 flex items-center gap-1 shadow-xl">
            <button
              id="btn-layer-moisture"
              onClick={() => setLayerMode('soil_moisture')}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                layerMode === 'soil_moisture' 
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/30' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Humedad del Suelo (Richards PDE)"
            >
              <Droplets className="w-3.5 h-3.5" />
              Humedad Suelo
            </button>
            <button
              id="btn-layer-biomass"
              onClick={() => setLayerMode('biomass')}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                layerMode === 'biomass' 
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Biomasa y Altura de Dosel"
            >
              <Layers className="w-3.5 h-3.5" />
              Biomasa
            </button>
            <button
              id="btn-layer-stress"
              onClick={() => setLayerMode('water_stress')}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                layerMode === 'water_stress' 
                  ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Índice de Estrés Térmico e Hídrico"
            >
              <Thermometer className="w-3.5 h-3.5" />
              Estrés CWSI
            </button>
          </div>

          {/* Sub-depth selector when soil moisture is active */}
          {layerMode === 'soil_moisture' && (
            <div className="p-1 rounded-xl bg-slate-950/80 backdrop-blur-md border border-slate-800 flex items-center gap-1 text-[11px]">
              <span className="text-slate-500 px-1.5">Profundidad:</span>
              <button
                onClick={() => setSelectedDepth('top')}
                className={`px-2 py-0.5 rounded-md font-mono ${
                  selectedDepth === 'top' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                0-30 cm
              </button>
              <button
                onClick={() => setSelectedDepth('mid')}
                className={`px-2 py-0.5 rounded-md font-mono ${
                  selectedDepth === 'mid' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                30-60 cm
              </button>
              <button
                onClick={() => setSelectedDepth('deep')}
                className={`px-2 py-0.5 rounded-md font-mono ${
                  selectedDepth === 'deep' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                60-100 cm
              </button>
            </div>
          )}
        </div>

        {/* Floating HUD Information Box */}
        {dailyRecord && (
          <div className="absolute bottom-16 left-4 z-10 p-3 rounded-2xl bg-slate-950/85 backdrop-blur-md border border-slate-800/80 shadow-2xl text-xs space-y-1.5 w-64 pointer-events-none">
            <div className="flex items-center justify-between pb-1 border-b border-slate-800">
              <span className="font-semibold text-slate-300 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-emerald-400" /> {dailyRecord.date}
              </span>
              <span className="font-mono text-slate-400">DAP {dailyRecord.dap}</span>
            </div>
            
            <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-slate-400 pt-0.5">
              <div>Humedad Top: <span className="font-mono text-cyan-300">{(dailyRecord.soilMoistureTop * 100).toFixed(1)}%</span></div>
              <div>Biomasa: <span className="font-mono text-emerald-300">{(dailyRecord.biomassKgHa / 1000).toFixed(1)} t/ha</span></div>
              <div>LAI (Área Foliar): <span className="font-mono text-slate-200">{dailyRecord.lai} m²/m²</span></div>
              <div>Raíz: <span className="font-mono text-amber-300">{dailyRecord.rootDepthCm} cm</span></div>
              <div>Transpiración: <span className="font-mono text-blue-300">{dailyRecord.transpirationMm} mm</span></div>
              <div>GDD Acum: <span className="font-mono text-slate-200">{dailyRecord.gddAccumulated}°C·d</span></div>
            </div>
          </div>
        )}

        {/* Camera Quick Controls */}
        <div className="absolute bottom-16 right-4 z-10 flex flex-col gap-1.5">
          <button
            onClick={() => setCameraMode('perspective')}
            className={`p-2 rounded-xl backdrop-blur-md border text-xs flex items-center justify-center transition-all ${
              cameraMode === 'perspective' 
                ? 'bg-emerald-600 text-white border-emerald-500 shadow-lg' 
                : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:text-white'
            }`}
            title="Vista 3D Orbital Libre"
          >
            <Compass className="w-4 h-4" />
          </button>
          <button
            onClick={() => setCameraMode('top_down')}
            className={`p-2 rounded-xl backdrop-blur-md border text-xs flex items-center justify-center transition-all ${
              cameraMode === 'top_down' 
                ? 'bg-emerald-600 text-white border-emerald-500 shadow-lg' 
                : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:text-white'
            }`}
            title="Vista Aérea Cenital (Nadir)"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowWireframe(!showWireframe)}
            className={`p-2 rounded-xl backdrop-blur-md border text-xs flex items-center justify-center transition-all ${
              showWireframe 
                ? 'bg-cyan-600 text-white border-cyan-500 shadow-lg' 
                : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:text-white'
            }`}
            title="Malla de Elementos Finitos (FEM)"
          >
            <Layers className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Bottom Timeline Scrubber & Playback Controls */}
      <div className="h-16 bg-slate-950/95 border-t border-slate-800 px-4 py-2 flex items-center gap-4 z-20">
        {/* Play/Pause Button */}
        <button
          id="btn-3d-play-toggle"
          onClick={() => setIsPlaying(!isPlaying)}
          disabled={!simulation}
          className="p-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white transition-all shadow-md shadow-emerald-600/30 disabled:opacity-50"
          title={isPlaying ? 'Pausar Simulación' : 'Reproducir Ciclo Fenológico'}
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </button>

        <button
          onClick={() => {
            setIsPlaying(false);
            onChangeDayIndex(0);
          }}
          disabled={!simulation}
          className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all disabled:opacity-50"
          title="Reiniciar a Siembra"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Day Slider */}
        <div className="flex-1 flex flex-col justify-center">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>DAP 1 (Siembra)</span>
            <span className="text-emerald-400 font-semibold">
              Día {currentDayIndex + 1} de {simulation?.dailyRecords.length || 120} ({dailyRecord?.date || '--'})
            </span>
            <span>Cosecha (R6)</span>
          </div>
          <input
            id="slider-timeline-dap"
            type="range"
            min={0}
            max={(simulation?.dailyRecords.length || 1) - 1}
            value={currentDayIndex}
            onChange={(e) => {
              setIsPlaying(false);
              onChangeDayIndex(parseInt(e.target.value, 10));
            }}
            disabled={!simulation}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500 hover:accent-emerald-400 transition-all"
          />
        </div>

        {/* Speed multiplier selector */}
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          {[1, 2, 4].map((speed) => (
            <button
              key={speed}
              onClick={() => setSpeedMultiplier(speed)}
              className={`px-2 py-1 rounded-lg font-mono transition-all ${
                speedMultiplier === speed ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
