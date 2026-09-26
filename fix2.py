import re

path = r'c:\Users\USERJSSV\Downloads\cerespinn---climate-adaptive-maize-digital-twin\src\components\ThreeFieldViewer.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add isFullscreen state
content = re.sub(
    r'(const \[layerMode, setLayerMode\] = useState<VisualLayerMode>\(\'soil_moisture\'\);)',
    r'\1\n  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);',
    content
)

# 2. Add toggleFullscreen and container classes
# The original container has h-[540px], we will change it to h-[700px] or h-[650px]
# Let's use h-[680px]
return_block = r'''  return (
    <div id="three-field-viewer-card" className="relative w-full h-\[540px\] bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden flex flex-col select-none">'''

new_return_block = r'''  useEffect(() => {
    const handleFullscreenChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.getElementById('three-field-viewer-card')?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  return (
    <div id="three-field-viewer-card" className={`relative w-full bg-white dark:bg-slate-900/90 shadow-2xl overflow-hidden flex flex-col select-none transition-all ${isFullscreen ? 'h-screen rounded-none border-none z-50' : 'h-[680px] rounded-2xl border border-slate-200 dark:border-slate-800'}`}>'''

content = re.sub(return_block, new_return_block, content)

# 3. Add button in Camera Quick Controls
btn_block = r'''        {/* Camera Quick Controls */}
        <div className="absolute bottom-16 right-4 z-10 flex flex-col gap-1.5">
          <button'''

new_btn_block = r'''        {/* Camera Quick Controls */}
        <div className="absolute bottom-16 right-4 z-10 flex flex-col gap-1.5">
          <button
            onClick={toggleFullscreen}
            className={`p-2 rounded-xl backdrop-blur-md border text-xs flex items-center justify-center transition-all ${isFullscreen ? 'bg-indigo-600 text-white border-indigo-500 shadow-lg' : 'bg-white/85 dark:bg-slate-950/80 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-white'}`}
            title="Pantalla Completa"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button'''

content = re.sub(btn_block, new_btn_block, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
