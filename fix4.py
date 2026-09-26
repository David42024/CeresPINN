path = r'c:\Users\USERJSSV\Downloads\cerespinn---climate-adaptive-maize-digital-twin\src\components\ThreeFieldViewer.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add rain refs
old_refs = "const plantsGroupRef = useRef<THREE.Group | null>(null);"
new_refs = "const plantsGroupRef = useRef<THREE.Group | null>(null);\n  const rainSystemRef = useRef<THREE.Points | null>(null);\n  const rainVelocitiesRef = useRef<number[]>([]);"
content = content.replace(old_refs, new_refs)

# 2. Add rain generation
old_render_loop = "    // Render loop"
new_render_loop = '''    // Rain system
    const rainCount = 1200;
    const rainGeometry = new THREE.BufferGeometry();
    const rainPositions = new Float32Array(rainCount * 3);
    const rainVelocities = [];
    for (let i = 0; i < rainCount; i++) {
      rainPositions[i * 3] = (Math.random() - 0.5) * 40;
      rainPositions[i * 3 + 1] = Math.random() * 20;
      rainPositions[i * 3 + 2] = (Math.random() - 0.5) * 40;
      rainVelocities.push(0.3 + Math.random() * 0.2);
    }
    rainGeometry.setAttribute('position', new THREE.BufferAttribute(rainPositions, 3));
    const rainMaterial = new THREE.PointsMaterial({
      color: 0x99ccff,
      size: 0.1,
      transparent: true,
      opacity: 0.6
    });
    const rainSystem = new THREE.Points(rainGeometry, rainMaterial);
    rainSystem.visible = false;
    scene.add(rainSystem);
    rainSystemRef.current = rainSystem;
    rainVelocitiesRef.current = rainVelocities;

    // Render loop'''
content = content.replace(old_render_loop, new_render_loop)

# 3. Add rain animation
old_animate = "        rendererRef.current.render(sceneRef.current, cameraRef.current);"
new_animate = '''        if (rainSystemRef.current && rainSystemRef.current.visible) {
          const positions = rainSystemRef.current.geometry.attributes.position.array as Float32Array;
          for (let i = 0; i < rainVelocitiesRef.current.length; i++) {
            positions[i * 3 + 1] -= rainVelocitiesRef.current[i];
            if (positions[i * 3 + 1] < 0) {
              positions[i * 3 + 1] = 20;
            }
          }
          rainSystemRef.current.geometry.attributes.position.needsUpdate = true;
        }
        rendererRef.current.render(sceneRef.current, cameraRef.current);'''
content = content.replace(old_animate, new_animate)

# 4. Toggle rain visibility
old_dep_array = "  }, [currentDayIndex, layerMode, showWireframe, simulation, selectedDepth]);"
new_dep_array = '''    // Update Rain
    if (rainSystemRef.current && dailyRecord) {
      if ((dailyRecord.precipitationMm || 0) > 0) {
        rainSystemRef.current.visible = true;
        const mat = rainSystemRef.current.material as THREE.PointsMaterial;
        mat.opacity = Math.min(0.8, 0.3 + (dailyRecord.precipitationMm / 40));
      } else {
        rainSystemRef.current.visible = false;
      }
    }
  }, [currentDayIndex, layerMode, showWireframe, simulation, selectedDepth]);'''
content = content.replace(old_dep_array, new_dep_array)

# 5. Fix ResizeObserver
old_resize = '''    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);'''

new_resize = '''    const resizeObserver = new ResizeObserver(() => handleResize());
    resizeObserver.observe(containerRef.current);
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();'''
content = content.replace(old_resize, new_resize)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
