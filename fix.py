import re
with open(r'c:\Users\USERJSSV\Downloads\cerespinn---climate-adaptive-maize-digital-twin\src\components\ThreeFieldViewer.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the main container div
content = re.sub(r'className=\{[\r\n]*elative w-full bg-white dark:bg-slate-900/90 shadow-2xl overflow-hidden flex flex-col select-none transition-all \}>', 'className={`relative w-full bg-white dark:bg-slate-900/90 shadow-2xl overflow-hidden flex flex-col select-none transition-all ${isFullscreen ? \'h-screen rounded-none border-none z-50\' : \'h-[540px] rounded-2xl border border-slate-200 dark:border-slate-800\'}`}>', content)

# Fix the button
content = re.sub(r'className=\{p-2 rounded-xl backdrop-blur-md border text-xs flex items-center justify-center transition-all \}', 'className={`p-2 rounded-xl backdrop-blur-md border text-xs flex items-center justify-center transition-all ${isFullscreen ? \'bg-indigo-600 text-white border-indigo-500 shadow-lg\' : \'bg-white/85 dark:bg-slate-950/80 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-white\'}`}', content)

with open(r'c:\Users\USERJSSV\Downloads\cerespinn---climate-adaptive-maize-digital-twin\src\components\ThreeFieldViewer.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix done")